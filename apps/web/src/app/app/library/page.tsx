"use client";

import React, { useEffect, useState, useMemo } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import {
  BookOpen,
  Library,
  BookCopy,
  Users,
  Repeat,
  BookmarkCheck,
  Coins,
  ShoppingCart,
  Layers,
  ClipboardCheck,
  Search,
  Plus,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  ChevronRight,
  Filter,
  BarChart3,
  Building,
  Check,
  X,
  ShieldAlert,
  FileText,
  DollarSign,
  Calendar,
  Sparkles,
  ArrowRight,
  AlertCircle,
  Eye,
  KeyRound,
  Download,
} from "lucide-react";
import type {
  LibraryBranchModel,
  LibraryLendingPolicyModel,
  LibraryCatalogItemModel,
  LibraryPhysicalCopyModel,
  LibraryMemberProfileModel,
  LibraryCirculationLoanModel,
  LibraryReservationModel,
  LibraryFineRecordModel,
  LibraryAcquisitionRequestModel,
  LibrarySubscriptionModel,
  LibraryInventoryAuditModel,
  LibraryAnalyticsSummaryModel,
  LibraryDeadlineSweepModel,
} from "@campusos/types";
import {
  LibraryBranchStatus,
  LibraryResourceType,
  LibraryCatalogStatus,
  LibraryCopyCondition,
  LibraryCirculationStatus,
  LibraryMemberCategory,
  LibraryMemberStatus,
  LibraryLoanStatus,
  LibraryReservationStatus,
  LibraryFineCategory,
  LibraryFineStatus,
  LibraryAcquisitionStatus,
  LibrarySubscriptionType,
  LibrarySubscriptionStatus,
  LibraryInventoryAuditStatus,
} from "@campusos/types";

export default function EnterpriseLibraryManagementPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<
    | "overview"
    | "catalog"
    | "inventory"
    | "circulation"
    | "members"
    | "reservations"
    | "fines"
    | "acquisitions"
    | "subscriptions"
    | "stock_audits"
  >("overview");

  // State Management
  const [analytics, setAnalytics] = useState<LibraryAnalyticsSummaryModel | null>(null);
  const [branches, setBranches] = useState<LibraryBranchModel[]>([]);
  const [catalogItems, setCatalogItems] = useState<LibraryCatalogItemModel[]>([]);
  const [physicalCopies, setPhysicalCopies] = useState<LibraryPhysicalCopyModel[]>([]);
  const [members, setMembers] = useState<LibraryMemberProfileModel[]>([]);
  const [loans, setLoans] = useState<LibraryCirculationLoanModel[]>([]);
  const [reservations, setReservations] = useState<LibraryReservationModel[]>([]);
  const [fines, setFines] = useState<LibraryFineRecordModel[]>([]);
  const [acquisitions, setAcquisitions] = useState<LibraryAcquisitionRequestModel[]>([]);
  const [subscriptions, setSubscriptions] = useState<LibrarySubscriptionModel[]>([]);
  const [audits, setAudits] = useState<LibraryInventoryAuditModel[]>([]);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);
  const [actionErrorMessage, setActionErrorMessage] = useState<string | null>(null);

  // Modals
  const [isNewBranchModalOpen, setIsNewBranchModalOpen] = useState(false);
  const [isNewCatalogModalOpen, setIsNewCatalogModalOpen] = useState(false);
  const [isNewCopyModalOpen, setIsNewCopyModalOpen] = useState(false);
  const [isCheckoutModalOpen, setIsCheckoutModalOpen] = useState(false);
  const [isReturnModalOpen, setIsReturnModalOpen] = useState(false);
  const [selectedLoanForReturn, setSelectedLoanForReturn] = useState<LibraryCirculationLoanModel | null>(null);
  const [isNewReservationModalOpen, setIsNewReservationModalOpen] = useState(false);
  const [isWaiveFineModalOpen, setIsWaiveFineModalOpen] = useState(false);
  const [selectedFineForWaiver, setSelectedFineForWaiver] = useState<LibraryFineRecordModel | null>(null);
  const [isNewAcquisitionModalOpen, setIsNewAcquisitionModalOpen] = useState(false);
  const [isNewSubscriptionModalOpen, setIsNewSubscriptionModalOpen] = useState(false);
  const [isNewAuditModalOpen, setIsNewAuditModalOpen] = useState(false);
  const [isAuditScanModalOpen, setIsAuditScanModalOpen] = useState(false);
  const [selectedAuditForScan, setSelectedAuditForScan] = useState<LibraryInventoryAuditModel | null>(null);

  // Form states
  const [branchForm, setBranchForm] = useState({
    branch_code: `LIB-${Math.floor(100 + Math.random() * 900)}`,
    name: "Central Learning Resource Centre",
    location_building: "Knowledge Tower",
    location_floor: "1st & 2nd Floor",
    contact_email: "library@campusos.edu",
    contact_phone: "+1 800 555 0199",
  });

  const [catalogForm, setCatalogForm] = useState({
    catalog_code: `CAT-${Math.floor(1000 + Math.random() * 9000)}`,
    title: "",
    authors_json: "",
    resource_type: LibraryResourceType.BOOK,
    isbn_or_issn: "",
    edition: "1st Edition",
    publisher: "CampusOS Academic Press",
    publication_year: new Date().getFullYear(),
    primary_language: "English",
    subject_classification: "Computer Science & Engineering",
    classification_number: "QA76.73.P98",
    dewey_decimal_class: "005.133",
    is_digital: false,
    digital_access_url: "",
  });

  const [copyForm, setCopyForm] = useState({
    accession_number: `ACC-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`,
    catalog_item_id: "",
    library_id: "",
    barcode_rfid: "",
    shelf_location: "Stack 4, Bay B",
    condition_grade: LibraryCopyCondition.NEW,
    price_cost: "45.00",
  });

  const [checkoutForm, setCheckoutForm] = useState({
    physical_copy_id: "",
    member_id: "",
    checkout_library_id: "",
    loan_duration_days: 14,
  });

  const [returnForm, setReturnForm] = useState({
    returned_to_library_id: "",
    observed_condition: LibraryCopyCondition.GOOD,
    damage_notes: "",
    assess_damage_fine: "0.00",
  });

  const [reservationForm, setReservationForm] = useState({
    catalog_item_id: "",
    member_id: "",
    pickup_library_id: "",
    priority_level: 1,
  });

  const [waiverForm, setWaiverForm] = useState({
    waived_amount: "5.00",
    waiver_reason: "Academic scholarship privilege & medical leave pardon.",
  });

  const [acquisitionForm, setAcquisitionForm] = useState({
    request_code: `ACQ-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
    title: "",
    author: "",
    isbn: "",
    publisher: "",
    edition_year: new Date().getFullYear(),
    quantity_requested: 2,
    estimated_total_cost: "120.00",
    currency: "USD",
    justification_notes: "Recommended textbook for upcoming Distributed Systems elective.",
  });

  const [subscriptionForm, setSubscriptionForm] = useState({
    subscription_code: `SUB-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
    publication_title: "",
    publisher_or_vendor: "",
    subscription_type: LibrarySubscriptionType.E_JOURNAL_PACKAGE,
    start_date: new Date().toISOString().split("T")[0],
    end_date: new Date(Date.now() + 365 * 86400000).toISOString().split("T")[0],
    annual_subscription_cost: "1500.00",
    currency: "USD",
    expected_issues_count: 12,
    digital_access_portal_url: "https://ieeexplore.ieee.org",
  });

  const [auditForm, setAuditForm] = useState({
    audit_code: `AUDIT-${new Date().getFullYear()}-${Math.floor(10 + Math.random() * 90)}`,
    audit_name: "Annual Physical Verification & RFID Audit",
    library_id: "",
    scope_notes: "100% stock count of General Reference and Engineering Stacks.",
  });

  const [auditScanForm, setAuditScanForm] = useState({
    scanned_accession_number: "",
    observed_condition: LibraryCopyCondition.GOOD,
    scan_location: "Engineering Stack Bay A",
  });

  // Fetch all data
  const fetchData = async () => {
    try {
      setIsRefreshing(true);
      const [
        analyticsRes,
        branchesRes,
        catalogRes,
        copiesRes,
        membersRes,
        loansRes,
        reservationsRes,
        finesRes,
        acquisitionsRes,
        subscriptionsRes,
        auditsRes,
      ] = await Promise.all([
        apiFetch<LibraryAnalyticsSummaryModel>("/api/v1/library/analytics/summary").catch(() => null),
        apiFetch<{ items: LibraryBranchModel[]; total: number }>("/api/v1/library/branches").catch(() => null),
        apiFetch<{ items: LibraryCatalogItemModel[]; total: number }>("/api/v1/library/catalog?limit=100").catch(() => null),
        apiFetch<{ items: LibraryPhysicalCopyModel[]; total: number }>("/api/v1/library/copies?limit=100").catch(() => null),
        apiFetch<{ items: LibraryMemberProfileModel[]; total: number }>("/api/v1/library/members?limit=100").catch(() => null),
        apiFetch<{ items: LibraryCirculationLoanModel[]; total: number }>("/api/v1/library/circulation/loans?limit=100").catch(() => null),
        apiFetch<{ items: LibraryReservationModel[]; total: number }>("/api/v1/library/reservations?limit=100").catch(() => null),
        apiFetch<{ items: LibraryFineRecordModel[]; total: number }>("/api/v1/library/fines?limit=100").catch(() => null),
        apiFetch<{ items: LibraryAcquisitionRequestModel[]; total: number }>("/api/v1/library/acquisitions?limit=100").catch(() => null),
        apiFetch<{ items: LibrarySubscriptionModel[]; total: number }>("/api/v1/library/subscriptions?limit=100").catch(() => null),
        apiFetch<{ items: LibraryInventoryAuditModel[]; total: number }>("/api/v1/library/inventory-audits?limit=50").catch(() => null),
      ]);

      if (analyticsRes?.data) setAnalytics(analyticsRes.data);
      if (branchesRes?.data?.items) setBranches(branchesRes.data.items);
      if (catalogRes?.data?.items) setCatalogItems(catalogRes.data.items);
      if (copiesRes?.data?.items) setPhysicalCopies(copiesRes.data.items);
      if (membersRes?.data?.items) setMembers(membersRes.data.items);
      if (loansRes?.data?.items) setLoans(loansRes.data.items);
      if (reservationsRes?.data?.items) setReservations(reservationsRes.data.items);
      if (finesRes?.data?.items) setFines(finesRes.data.items);
      if (acquisitionsRes?.data?.items) setAcquisitions(acquisitionsRes.data.items);
      if (subscriptionsRes?.data?.items) setSubscriptions(subscriptionsRes.data.items);
      if (auditsRes?.data?.items) setAudits(auditsRes.data.items);
    } catch (err: any) {
      console.error("Error fetching library data:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const triggerComplianceSweep = async () => {
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      const res = await apiFetch<LibraryDeadlineSweepModel>("/api/v1/library/compliance/sweep", {
        method: "POST",
      });
      if (res?.data) {
        setActionSuccessMessage(
          `Compliance sweep completed successfully! Processed ${res.data.overdue_loans_flagged} overdue loans (computed $${res.data.fines_computed_amount} in fines), expired ${res.data.expired_reservations_released} holds, and flagged ${res.data.expiring_subscriptions_flagged} expiring serials.`
        );
      }
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to trigger library sweep");
    }
  };

  // Create Branch Handler
  const handleCreateBranch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch("/api/v1/library/branches", {
        method: "POST",
        body: JSON.stringify(branchForm),
      });
      setActionSuccessMessage(`Branch '${branchForm.name}' created successfully.`);
      setIsNewBranchModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to create library branch.");
    }
  };

  // Create Catalog Title Handler
  const handleCreateCatalog = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      const authors = catalogForm.authors_json
        .split(",")
        .map((a) => a.trim())
        .filter(Boolean);
      await apiFetch("/api/v1/library/catalog", {
        method: "POST",
        body: JSON.stringify({
          ...catalogForm,
          authors_json: authors.length > 0 ? authors : ["CampusOS Faculty"],
          publication_year: Number(catalogForm.publication_year) || new Date().getFullYear(),
        }),
      });
      setActionSuccessMessage(`Bibliographic item '${catalogForm.title}' added to institutional OPAC.`);
      setIsNewCatalogModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to create catalog entry.");
    }
  };

  // Register Physical Copy Handler
  const handleRegisterCopy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch("/api/v1/library/copies", {
        method: "POST",
        body: JSON.stringify({
          ...copyForm,
          price_cost: Number(copyForm.price_cost) || 0,
        }),
      });
      setActionSuccessMessage(`Physical copy '${copyForm.accession_number}' accessioned into inventory.`);
      setIsNewCopyModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to register physical copy.");
    }
  };

  // Checkout Loan Handler
  const handleCheckoutLoan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch("/api/v1/library/circulation/checkout", {
        method: "POST",
        body: JSON.stringify(checkoutForm),
      });
      setActionSuccessMessage("Resource copy checked out successfully.");
      setIsCheckoutModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Checkout failed. Verify patron eligibility and copy availability.");
    }
  };

  // Return Loan Handler
  const handleReturnLoan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLoanForReturn) return;
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch(`/api/v1/library/circulation/loans/${selectedLoanForReturn.id}/return`, {
        method: "POST",
        body: JSON.stringify({
          ...returnForm,
          assess_damage_fine: Number(returnForm.assess_damage_fine) || 0,
        }),
      });
      setActionSuccessMessage("Item checked in. Fines calculated and hold queue allocated.");
      setIsReturnModalOpen(false);
      setSelectedLoanForReturn(null);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to complete book return check-in.");
    }
  };

  // Renew Loan Handler
  const handleRenewLoan = async (loanId: string) => {
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch(`/api/v1/library/circulation/loans/${loanId}/renew`, {
        method: "POST",
        body: JSON.stringify({ additional_days: 14 }),
      });
      setActionSuccessMessage("Loan successfully renewed with extended due date.");
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Renewal denied. Verify renewal limits and reservation queue.");
    }
  };

  // Place Reservation Handler
  const handlePlaceReservation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch("/api/v1/library/reservations", {
        method: "POST",
        body: JSON.stringify(reservationForm),
      });
      setActionSuccessMessage("Reservation hold placed. Patron placed into priority waitlist.");
      setIsNewReservationModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Reservation failed.");
    }
  };

  // Waive Fine Handler
  const handleWaiveFine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFineForWaiver) return;
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch(`/api/v1/library/fines/${selectedFineForWaiver.id}/waive`, {
        method: "POST",
        body: JSON.stringify({
          waived_amount: Number(waiverForm.waived_amount),
          waiver_reason: waiverForm.waiver_reason,
        }),
      });
      setActionSuccessMessage(`Fine waived. Audit entry recorded for compliance.`);
      setIsWaiveFineModalOpen(false);
      setSelectedFineForWaiver(null);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to waive fine.");
    }
  };

  // Create Acquisition Handler
  const handleCreateAcquisition = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch("/api/v1/library/acquisitions", {
        method: "POST",
        body: JSON.stringify({
          ...acquisitionForm,
          quantity_requested: Number(acquisitionForm.quantity_requested) || 1,
          estimated_total_cost: Number(acquisitionForm.estimated_total_cost) || 0,
        }),
      });
      setActionSuccessMessage("Acquisition purchase request logged for librarian review.");
      setIsNewAcquisitionModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to log acquisition request.");
    }
  };

  // Review Acquisition (Approve/Reject)
  const handleReviewAcquisition = async (acqId: string, status: "APPROVED" | "REJECTED") => {
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch(`/api/v1/library/acquisitions/${acqId}/review`, {
        method: "POST",
        body: JSON.stringify({
          status,
          decision_notes: `Decision recorded via Library Admin Console on ${new Date().toLocaleDateString()}`,
        }),
      });
      setActionSuccessMessage(`Acquisition request marked as ${status}.`);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to update acquisition status.");
    }
  };

  // Create Subscription Handler
  const handleCreateSubscription = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch("/api/v1/library/subscriptions", {
        method: "POST",
        body: JSON.stringify({
          ...subscriptionForm,
          annual_subscription_cost: Number(subscriptionForm.annual_subscription_cost) || 0,
          expected_issues_count: Number(subscriptionForm.expected_issues_count) || 12,
        }),
      });
      setActionSuccessMessage("Serial / Periodical subscription activated.");
      setIsNewSubscriptionModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to register subscription.");
    }
  };

  // Start Audit Handler
  const handleStartAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch("/api/v1/library/inventory-audits", {
        method: "POST",
        body: JSON.stringify(auditForm),
      });
      setActionSuccessMessage("Stock verification audit initiated. Snapshot captured.");
      setIsNewAuditModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to start stock audit.");
    }
  };

  // Record Audit Scan Handler
  const handleRecordAuditScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAuditForScan) return;
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      await apiFetch(`/api/v1/library/inventory-audits/${selectedAuditForScan.id}/record-scan`, {
        method: "POST",
        body: JSON.stringify(auditScanForm),
      });
      setActionSuccessMessage(`Accession '${auditScanForm.scanned_accession_number}' verified in physical stock.`);
      setAuditScanForm({ ...auditScanForm, scanned_accession_number: "" });
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Audit scan recording failed.");
    }
  };

  // Digital Token Generator
  const handleGenerateDigitalToken = async (catalogItemId: string) => {
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      const res = await apiFetch<{ download_token: string; access_url: string }>(
        `/api/v1/library/digital-access/${catalogItemId}/token`,
        { method: "POST" }
      );
      if (res?.data) {
        setActionSuccessMessage(`Digital token issued: ${res.data.download_token}. Opening resource...`);
        window.open(res.data.access_url, "_blank");
      }
    } catch (err: any) {
      setActionErrorMessage(err.message || "Digital token generation failed.");
    }
  };

  // Filtered views
  const filteredCatalog = useMemo(() => {
    return catalogItems.filter((item) => {
      const matchQuery =
        !searchQuery ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.catalog_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (item.isbn_or_issn && item.isbn_or_issn.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (item.subject_classification && item.subject_classification.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchFilter = filterCategory === "ALL" || item.resource_type === filterCategory;
      return matchQuery && matchFilter;
    });
  }, [catalogItems, searchQuery, filterCategory]);

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Top Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <BookOpen className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  Enterprise Library & Learning Resources Management
                </h1>
                <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Step 45
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-1">
                Institutional OPAC, multi-branch circulation desk, patron eligibility control, automated fine & waiver ledger, serials & stock verification.
              </p>
            </div>
          </div>
        </div>

        {/* Global Controls & Sweep Action */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={fetchData}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={triggerComplianceSweep}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition"
          >
            <Sparkles className="h-3.5 w-3.5" />
            Run Compliance Sweep
          </button>
          <button
            onClick={() => setIsCheckoutModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 transition"
          >
            <Repeat className="h-3.5 w-3.5" />
            Circulation Checkout
          </button>
        </div>
      </div>

      {/* Notifications / Alerts */}
      {actionSuccessMessage && (
        <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-200 text-sm">
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
        <div className="flex items-center justify-between p-4 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-200 text-sm">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0" />
            <span>{actionErrorMessage}</span>
          </div>
          <button onClick={() => setActionErrorMessage(null)} className="text-rose-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Tab Navigation (10 Core Operational Tabs) */}
      <div className="flex items-center gap-1 overflow-x-auto border-b border-slate-800 pb-2 scrollbar-none">
        {[
          { id: "overview", label: "Overview & Analytics", icon: BarChart3 },
          { id: "catalog", label: "OPAC Catalog", icon: BookOpen },
          { id: "inventory", label: "Physical Inventory", icon: BookCopy },
          { id: "circulation", label: "Circulation Desk", icon: Repeat },
          { id: "members", label: "Patron Members", icon: Users },
          { id: "reservations", label: "Hold Queues", icon: BookmarkCheck },
          { id: "fines", label: "Fines & Waivers", icon: Coins },
          { id: "acquisitions", label: "Acquisitions", icon: ShoppingCart },
          { id: "subscriptions", label: "Periodicals & Serials", icon: Layers },
          { id: "stock_audits", label: "Stock Audits", icon: ClipboardCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                isActive
                  ? "bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* 1. OVERVIEW & ANALYTICS TAB */}
      {/* ========================================================================= */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Analytics KPI Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase text-slate-400">Total Bibliographic Titles</span>
                <BookOpen className="h-4 w-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-white mt-2">
                {analytics?.total_catalog_titles ?? catalogItems.length}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {analytics?.total_subscriptions ?? subscriptions.length} Active Serials & Subscriptions
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase text-slate-400">Physical Copies in Stock</span>
                <BookCopy className="h-4 w-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white mt-2">
                {analytics?.total_physical_copies ?? physicalCopies.length}
              </div>
              <div className="text-xs text-emerald-400 mt-1">
                {analytics?.available_copies ?? physicalCopies.filter(c => c.circulation_status === LibraryCirculationStatus.AVAILABLE).length} available for loan
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase text-slate-400">Active Circulation Loans</span>
                <Repeat className="h-4 w-4 text-cyan-400" />
              </div>
              <div className="text-2xl font-bold text-white mt-2">
                {analytics?.total_active_loans ?? loans.filter((l) => l.status === LibraryLoanStatus.ACTIVE).length}
              </div>
              <div className="text-xs text-rose-400 mt-1">
                {analytics?.total_overdue_loans ?? 0} overdue ({analytics?.circulation_rate_percentage ?? 0}% circulation rate)
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase text-slate-400">Fine Balance Pending</span>
                <Coins className="h-4 w-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-white mt-2">
                ${analytics?.total_outstanding_fines ? Number(analytics.total_outstanding_fines).toFixed(2) : "0.00"}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {reservations.filter((r) => r.status === LibraryReservationStatus.WAITING).length} pending hold reservations
              </div>
            </div>
          </div>

          {/* Quick Action Operations Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Library Branches Summary */}
            <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Library className="h-4 w-4 text-indigo-400" />
                  Institutional Branches ({branches.length})
                </h3>
                <button
                  onClick={() => setIsNewBranchModalOpen(true)}
                  className="px-2.5 py-1 text-[11px] font-medium rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30"
                >
                  + Add Branch
                </button>
              </div>
              <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                {branches.length === 0 ? (
                  <div className="text-xs text-slate-500 text-center py-6">No branches registered yet.</div>
                ) : (
                  branches.map((b) => (
                    <div
                      key={b.id}
                      className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                    >
                      <div>
                        <div className="text-xs font-semibold text-slate-200">{b.name}</div>
                        <div className="text-[11px] text-slate-500">
                          {b.branch_code} • {b.location_building || "Main Campus"}
                        </div>
                      </div>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-semibold rounded-full border ${
                          b.status === LibraryBranchStatus.ACTIVE
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : "bg-slate-500/10 text-slate-400 border-slate-500/30"
                        }`}
                      >
                        {b.status}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Hold Reservation & Circulation Queue */}
            <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <BookmarkCheck className="h-4 w-4 text-amber-400" />
                  Active Hold Queues ({reservations.length})
                </h3>
                <button
                  onClick={() => setActiveTab("reservations")}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                >
                  View All <ChevronRight className="h-3 w-3" />
                </button>
              </div>
              <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                {reservations.slice(0, 4).map((r) => (
                  <div
                    key={r.id}
                    className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-200">Queue #{r.queue_position}</div>
                      <div className="text-[11px] text-slate-500">
                        Expires: {r.pickup_deadline ? new Date(r.pickup_deadline).toLocaleDateString() : (r.expired_at ? new Date(r.expired_at).toLocaleDateString() : "Pending Allocation")}
                      </div>
                    </div>
                    <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30">
                      {r.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Active Inventory Verification Audits */}
            <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <ClipboardCheck className="h-4 w-4 text-cyan-400" />
                  Stock Audits & Verification
                </h3>
                <button
                  onClick={() => setIsNewAuditModalOpen(true)}
                  className="px-2.5 py-1 text-[11px] font-medium rounded-lg bg-cyan-600/20 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-600/30"
                >
                  + Start Audit
                </button>
              </div>
              <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                {audits.slice(0, 3).map((a) => (
                  <div
                    key={a.id}
                    className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-200">{a.title}</div>
                      <div className="text-[11px] text-slate-500">
                        {a.audit_code} • Expected: {a.total_expected_copies} • Scanned: {a.verified_present_copies}
                      </div>
                    </div>
                    <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                      {a.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. OPAC CATALOG TAB */}
      {/* ========================================================================= */}
      {activeTab === "catalog" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <div className="flex flex-1 items-center gap-3">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search titles, authors, ISBN, call numbers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none"
              >
                <option value="ALL">All Resource Types</option>
                {Object.values(LibraryResourceType).map((rt) => (
                  <option key={rt} value={rt}>{rt}</option>
                ))}
              </select>
            </div>
            <button
              onClick={() => setIsNewCatalogModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Catalog Title
            </button>
          </div>

          {/* Catalog Titles Table */}
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Title & Details</th>
                  <th className="py-3 px-4">Catalog Code / ISBN</th>
                  <th className="py-3 px-4">Type & Classification</th>
                  <th className="py-3 px-4">Digital / Physical</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredCatalog.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-slate-500">
                      No catalog titles found matching query.
                    </td>
                  </tr>
                ) : (
                  filteredCatalog.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white">{item.title}</div>
                        <div className="text-[11px] text-slate-400">
                          by {(item.authors_json || []).join(", ") || "Unknown Author"} • {item.publisher} ({item.publication_year})
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-mono text-indigo-400">{item.catalog_code}</div>
                        <div className="text-[11px] text-slate-500">{item.isbn_or_issn || "No ISBN"}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-medium">
                          {item.resource_type}
                        </span>
                        <div className="text-[11px] text-slate-500 mt-1">{item.classification_number || "Call Number N/A"}</div>
                      </td>
                      <td className="py-3 px-4">
                        {item.is_digital ? (
                          <span className="inline-flex items-center gap-1 text-[11px] text-cyan-400">
                            <KeyRound className="h-3 w-3" /> Digital Access
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-400">Physical Copies</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {item.is_digital && (
                            <button
                              onClick={() => handleGenerateDigitalToken(item.id)}
                              className="px-2.5 py-1 text-[11px] rounded bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30 border border-cyan-500/30"
                              title="Generate secure digital access token"
                            >
                              Access E-Book
                            </button>
                          )}
                          <button
                            onClick={() => {
                              setCopyForm({ ...copyForm, catalog_item_id: item.id });
                              setIsNewCopyModalOpen(true);
                            }}
                            className="px-2.5 py-1 text-[11px] rounded bg-slate-800 hover:bg-slate-700 text-slate-200"
                          >
                            + Copy
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

      {/* ========================================================================= */}
      {/* 3. PHYSICAL INVENTORY TAB */}
      {/* ========================================================================= */}
      {activeTab === "inventory" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white">Physical Copy Registry & Accession Ledger</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Every physical copy tracked by barcode/RFID, shelf location, and condition assessment.
              </p>
            </div>
            <button
              onClick={() => setIsNewCopyModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20"
            >
              <Plus className="h-3.5 w-3.5" />
              Register Physical Copy
            </button>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Accession / Barcode</th>
                  <th className="py-3 px-4">Shelf Location</th>
                  <th className="py-3 px-4">Condition Grade</th>
                  <th className="py-3 px-4">Circulation Status</th>
                  <th className="py-3 px-4">Price / Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {physicalCopies.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-slate-500">
                      No physical copies registered yet.
                    </td>
                  </tr>
                ) : (
                  physicalCopies.map((copy) => (
                    <tr key={copy.id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4">
                        <div className="font-mono font-bold text-white">{copy.accession_number}</div>
                        <div className="text-[11px] text-slate-500">Barcode: {copy.barcode || copy.rfid_tag || "N/A"}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{copy.shelf_location || "General Stacks"}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 font-medium text-slate-300">
                          {copy.condition_grade}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            copy.circulation_status === LibraryCirculationStatus.AVAILABLE
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : copy.circulation_status === LibraryCirculationStatus.CHECKED_OUT
                              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
                              : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                          }`}
                        >
                          {copy.circulation_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        ${copy.purchase_price ? Number(copy.purchase_price).toFixed(2) : "0.00"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. CIRCULATION DESK TAB */}
      {/* ========================================================================= */}
      {activeTab === "circulation" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white">Circulation Desk: Issues, Returns & Renewals</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Active loans, overdue monitoring, automated fine assessments, and reservation queues.
              </p>
            </div>
            <button
              onClick={() => setIsCheckoutModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20"
            >
              <Repeat className="h-3.5 w-3.5" />
              Check Out Resource
            </button>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Loan Reference</th>
                  <th className="py-3 px-4">Issued At</th>
                  <th className="py-3 px-4">Due Date</th>
                  <th className="py-3 px-4">Renewal Count</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {loans.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-slate-500">
                      No circulation loans on record.
                    </td>
                  </tr>
                ) : (
                  loans.map((loan) => (
                    <tr key={loan.id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4">
                        <div className="font-mono font-bold text-white">{loan.loan_reference_code}</div>
                        <div className="text-[11px] text-slate-500">Copy ID: {loan.copy_id ? loan.copy_id.slice(0, 8) : "N/A"}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {new Date(loan.issued_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 font-mono font-medium text-slate-200">
                        {new Date(loan.due_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-slate-400">{loan.renewal_count} times</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            loan.status === LibraryLoanStatus.ACTIVE
                              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
                              : loan.status === LibraryLoanStatus.RETURNED
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          }`}
                        >
                          {loan.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {loan.status === LibraryLoanStatus.ACTIVE && (
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleRenewLoan(loan.id)}
                              className="px-2.5 py-1 text-[11px] rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                            >
                              Renew
                            </button>
                            <button
                              onClick={() => {
                                setSelectedLoanForReturn(loan);
                                setIsReturnModalOpen(true);
                              }}
                              className="px-2.5 py-1 text-[11px] rounded bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30 border border-emerald-500/30"
                            >
                              Check In
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. PATRON MEMBERS TAB */}
      {/* ========================================================================= */}
      {activeTab === "members" && (
        <div className="space-y-4">
          <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <h3 className="text-sm font-semibold text-white">Patron Membership Directory</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Role-based lending limits, overdue loan restrictions, and active borrower profiles.
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Membership #</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Borrowing Limits</th>
                  <th className="py-3 px-4">Current Active Loans</th>
                  <th className="py-3 px-4">Fines Due</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {members.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-slate-500">
                      No library patron profiles registered.
                    </td>
                  </tr>
                ) : (
                  members.map((member) => (
                    <tr key={member.id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-white">
                        {member.membership_number}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-indigo-950/60 text-indigo-300 border border-indigo-500/30 font-medium">
                          {member.member_category}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        Limit Override: {member.max_borrow_limit_override ?? "Standard Rules"}
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-semibold text-cyan-400">{member.current_active_loans}</span> active
                        {member.is_borrowing_suspended && (
                          <span className="text-rose-400 ml-1.5 font-bold">(Suspended)</span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-amber-400">
                        ${member.current_outstanding_fines ? Number(member.current_outstanding_fines).toFixed(2) : "0.00"}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            member.status === LibraryMemberStatus.ACTIVE
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          }`}
                        >
                          {member.status}
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

      {/* ========================================================================= */}
      {/* 6. HOLD RESERVATIONS TAB */}
      {/* ========================================================================= */}
      {activeTab === "reservations" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white">Hold Waitlist & Reservation Queue</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                FIFO and priority-tiered reservation queues automatically allocated upon book check-in.
              </p>
            </div>
            <button
              onClick={() => setIsNewReservationModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20"
            >
              <BookmarkCheck className="h-3.5 w-3.5" />
              Place Hold Reservation
            </button>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Queue #</th>
                  <th className="py-3 px-4">Priority Level</th>
                  <th className="py-3 px-4">Reservation Date</th>
                  <th className="py-3 px-4">Expiry Date</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {reservations.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-slate-500">
                      No active hold reservations in queue.
                    </td>
                  </tr>
                ) : (
                  reservations.map((res) => (
                    <tr key={res.id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-amber-400">
                        Position #{res.queue_position}
                      </td>
                      <td className="py-3 px-4 text-slate-300">Rank {res.priority_rank}</td>
                      <td className="py-3 px-4 text-slate-400">
                        {new Date(res.placed_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {res.pickup_deadline ? new Date(res.pickup_deadline).toLocaleDateString() : (res.expired_at ? new Date(res.expired_at).toLocaleDateString() : "Pending Allocation")}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            res.status === LibraryReservationStatus.ALLOCATED_PENDING_PICKUP
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : res.status === LibraryReservationStatus.WAITING
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                              : "bg-slate-500/10 text-slate-400 border-slate-500/30"
                          }`}
                        >
                          {res.status}
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

      {/* ========================================================================= */}
      {/* 7. FINES & WAIVERS TAB */}
      {/* ========================================================================= */}
      {activeTab === "fines" && (
        <div className="space-y-4">
          <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <h3 className="text-sm font-semibold text-white">Fine Assessment & Waiver Audit Ledger</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Daily overdue fines, lost book replacement costs, and audited staff waiver authorizations.
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Fine Reference</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Assessed Amount</th>
                  <th className="py-3 px-4">Amount Waived</th>
                  <th className="py-3 px-4">Amount Paid</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {fines.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-slate-500">
                      No outstanding fine assessments found.
                    </td>
                  </tr>
                ) : (
                  fines.map((fine) => (
                    <tr key={fine.id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-white">
                        {fine.fine_reference_code}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-medium">
                          {fine.fine_category}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-rose-400 font-bold">
                        ${Number(fine.base_amount).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 font-mono text-emerald-400">
                        ${Number(fine.waived_amount || 0).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        ${Number(fine.final_payable_amount || 0).toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            fine.fine_status === LibraryFineStatus.PAID
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : fine.fine_status === LibraryFineStatus.WAIVED
                              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          }`}
                        >
                          {fine.fine_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {fine.fine_status === LibraryFineStatus.ASSESSED && (
                          <button
                            onClick={() => {
                              setSelectedFineForWaiver(fine);
                              setIsWaiveFineModalOpen(true);
                            }}
                            className="px-2.5 py-1 text-[11px] rounded bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30"
                          >
                            Waive Fine
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 8. ACQUISITIONS TAB */}
      {/* ========================================================================= */}
      {activeTab === "acquisitions" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white">Acquisitions & Purchase Requests</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Faculty suggestions, procurement workflows, budget approvals, and automatic accessioning.
              </p>
            </div>
            <button
              onClick={() => setIsNewAcquisitionModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20"
            >
              <ShoppingCart className="h-3.5 w-3.5" />
              New Purchase Request
            </button>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Request Code & Title</th>
                  <th className="py-3 px-4">Author / ISBN</th>
                  <th className="py-3 px-4">Qty & Cost</th>
                  <th className="py-3 px-4">Approval Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {acquisitions.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-slate-500">
                      No acquisition requests logged.
                    </td>
                  </tr>
                ) : (
                  acquisitions.map((acq) => (
                    <tr key={acq.id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white">{acq.title}</div>
                        <div className="font-mono text-[11px] text-indigo-400">{acq.request_code}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {acq.author || "N/A"} • {acq.isbn_or_issn || "No ISBN"}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {acq.number_of_copies} copies • ${Number(acq.total_estimated_cost || 0).toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            acq.approval_status === LibraryAcquisitionStatus.APPROVED
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : acq.approval_status === LibraryAcquisitionStatus.REQUESTED
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                              : acq.approval_status === LibraryAcquisitionStatus.RECEIVED
                              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          }`}
                        >
                          {acq.approval_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {acq.approval_status === LibraryAcquisitionStatus.REQUESTED && (
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleReviewAcquisition(acq.id, "APPROVED")}
                              className="px-2 py-1 text-[11px] rounded bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30 border border-emerald-500/30"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReviewAcquisition(acq.id, "REJECTED")}
                              className="px-2 py-1 text-[11px] rounded bg-rose-600/20 text-rose-300 hover:bg-rose-600/30 border border-rose-500/30"
                            >
                              Reject
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 9. PERIODICALS & SUBSCRIPTIONS TAB */}
      {/* ========================================================================= */}
      {activeTab === "subscriptions" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white">Periodicals, Journals & Database Subscriptions</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Annual license expirations, vendor renewals, issue receipt tracking, and digital access portal links.
              </p>
            </div>
            <button
              onClick={() => setIsNewSubscriptionModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20"
            >
              <Plus className="h-3.5 w-3.5" />
              New Subscription
            </button>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Publication Title & Code</th>
                  <th className="py-3 px-4">Publisher / Vendor</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Term & Expiration</th>
                  <th className="py-3 px-4">Annual Cost</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Portal Access</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {subscriptions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-slate-500">
                      No serial subscriptions registered.
                    </td>
                  </tr>
                ) : (
                  subscriptions.map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white">{sub.publication_title}</div>
                        <div className="font-mono text-[11px] text-indigo-400">{sub.subscription_code}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{sub.publisher_or_vendor}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 font-medium text-slate-300">
                          {sub.subscription_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-mono">
                        {new Date(sub.end_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        ${Number(sub.annual_subscription_cost).toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          {sub.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {sub.digital_access_portal_url && (
                          <a
                            href={sub.digital_access_portal_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] rounded bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30"
                          >
                            Open Portal <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 10. STOCK VERIFICATION AUDITS TAB */}
      {/* ========================================================================= */}
      {activeTab === "stock_audits" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white">Annual Stock Verification & Inventory Audits</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Physical barcode/RFID inventory reconciliation, missing books tracking, and sign-off compliance.
              </p>
            </div>
            <button
              onClick={() => setIsNewAuditModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20"
            >
              <ClipboardCheck className="h-3.5 w-3.5" />
              Initiate Stock Audit
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {audits.map((audit) => (
              <div
                key={audit.id}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-slate-700 transition"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-cyan-400 font-bold">{audit.audit_code}</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                      {audit.status}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-white mt-1.5">{audit.title}</h4>
                  <p className="text-xs text-slate-400 mt-1">{audit.audit_scope || "Comprehensive stack verification."}</p>
                </div>

                <div className="grid grid-cols-3 gap-2 py-2 border-y border-slate-800 text-center font-mono">
                  <div>
                    <div className="text-[10px] uppercase text-slate-500">Expected</div>
                    <div className="text-sm font-bold text-slate-200">{audit.total_expected_copies}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-slate-500">Scanned</div>
                    <div className="text-sm font-bold text-emerald-400">{audit.verified_present_copies}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-slate-500">Missing</div>
                    <div className="text-sm font-bold text-rose-400">{audit.missing_copies_count}</div>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-1">
                  <button
                    onClick={() => {
                      setSelectedAuditForScan(audit);
                      setIsAuditScanModalOpen(true);
                    }}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30"
                  >
                    Scan Accession
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL DIALOGS */}
      {/* ========================================================================= */}

      {/* 1. New Branch Modal */}
      {isNewBranchModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Library className="h-5 w-5 text-indigo-400" />
                Add Institutional Library Branch
              </h3>
              <button onClick={() => setIsNewBranchModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleCreateBranch} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Branch Code</label>
                <input
                  type="text"
                  required
                  value={branchForm.branch_code}
                  onChange={(e) => setBranchForm({ ...branchForm, branch_code: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Branch Name</label>
                <input
                  type="text"
                  required
                  value={branchForm.name}
                  onChange={(e) => setBranchForm({ ...branchForm, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Building</label>
                  <input
                    type="text"
                    value={branchForm.location_building}
                    onChange={(e) => setBranchForm({ ...branchForm, location_building: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Floor</label>
                  <input
                    type="text"
                    value={branchForm.location_floor}
                    onChange={(e) => setBranchForm({ ...branchForm, location_floor: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewBranchModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Create Branch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 2. New Catalog Title Modal */}
      {isNewCatalogModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-xl rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl my-8">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-indigo-400" />
                Add Bibliographic Catalog Title (OPAC)
              </h3>
              <button onClick={() => setIsNewCatalogModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleCreateCatalog} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Catalog Code</label>
                  <input
                    type="text"
                    required
                    value={catalogForm.catalog_code}
                    onChange={(e) => setCatalogForm({ ...catalogForm, catalog_code: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">ISBN / ISSN</label>
                  <input
                    type="text"
                    value={catalogForm.isbn_or_issn}
                    onChange={(e) => setCatalogForm({ ...catalogForm, isbn_or_issn: e.target.value })}
                    placeholder="978-0134685991"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Title</label>
                <input
                  type="text"
                  required
                  placeholder="Principles of Database Systems"
                  value={catalogForm.title}
                  onChange={(e) => setCatalogForm({ ...catalogForm, title: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Authors (comma separated)</label>
                <input
                  type="text"
                  placeholder="Jeffrey Ullman, Alfred Aho"
                  value={catalogForm.authors_json}
                  onChange={(e) => setCatalogForm({ ...catalogForm, authors_json: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Resource Type</label>
                  <select
                    value={catalogForm.resource_type}
                    onChange={(e) => setCatalogForm({ ...catalogForm, resource_type: e.target.value as any })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    {Object.values(LibraryResourceType).map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Call Number / Dewey</label>
                  <input
                    type="text"
                    value={catalogForm.classification_number}
                    onChange={(e) => setCatalogForm({ ...catalogForm, classification_number: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="is_digital"
                  checked={catalogForm.is_digital}
                  onChange={(e) => setCatalogForm({ ...catalogForm, is_digital: e.target.checked })}
                  className="rounded bg-slate-950 border-slate-800 text-indigo-600"
                />
                <label htmlFor="is_digital" className="text-slate-300">
                  Enable Digital E-Resource Access (Secure Token Download)
                </label>
              </div>
              {catalogForm.is_digital && (
                <div>
                  <label className="block text-slate-400 mb-1">Digital Resource Access URL / Asset URI</label>
                  <input
                    type="text"
                    placeholder="https://library.campusos.internal/digital/ebook.pdf"
                    value={catalogForm.digital_access_url}
                    onChange={(e) => setCatalogForm({ ...catalogForm, digital_access_url: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              )}
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewCatalogModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Add Title
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 3. Register Physical Copy Modal */}
      {isNewCopyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BookCopy className="h-5 w-5 text-indigo-400" />
                Accession Physical Copy into Inventory
              </h3>
              <button onClick={() => setIsNewCopyModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleRegisterCopy} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Catalog Item Title</label>
                <select
                  required
                  value={copyForm.catalog_item_id}
                  onChange={(e) => setCopyForm({ ...copyForm, catalog_item_id: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                >
                  <option value="">Select Catalog Item...</option>
                  {catalogItems.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title} ({c.catalog_code})
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Accession Number</label>
                  <input
                    type="text"
                    required
                    value={copyForm.accession_number}
                    onChange={(e) => setCopyForm({ ...copyForm, accession_number: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Barcode / RFID Tag</label>
                  <input
                    type="text"
                    value={copyForm.barcode_rfid}
                    onChange={(e) => setCopyForm({ ...copyForm, barcode_rfid: e.target.value })}
                    placeholder="TAG-998822"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Owning Branch</label>
                  <select
                    required
                    value={copyForm.library_id}
                    onChange={(e) => setCopyForm({ ...copyForm, library_id: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    <option value="">Select Branch...</option>
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Condition Grade</label>
                  <select
                    value={copyForm.condition_grade}
                    onChange={(e) => setCopyForm({ ...copyForm, condition_grade: e.target.value as any })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    {Object.values(LibraryCopyCondition).map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewCopyModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Accession Copy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 4. Checkout Loan Modal */}
      {isCheckoutModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Repeat className="h-5 w-5 text-indigo-400" />
                Circulation Desk: Check Out Resource
              </h3>
              <button onClick={() => setIsCheckoutModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleCheckoutLoan} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Physical Copy</label>
                <select
                  required
                  value={checkoutForm.physical_copy_id}
                  onChange={(e) => setCheckoutForm({ ...checkoutForm, physical_copy_id: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                >
                  <option value="">Select Available Copy...</option>
                  {physicalCopies
                    .filter((c) => c.circulation_status === LibraryCirculationStatus.AVAILABLE)
                    .map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.accession_number} ({c.shelf_location || "Stacks"})
                      </option>
                    ))}
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Borrower Patron (Member)</label>
                <select
                  required
                  value={checkoutForm.member_id}
                  onChange={(e) => setCheckoutForm({ ...checkoutForm, member_id: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                >
                  <option value="">Select Patron Profile...</option>
                  {members
                    .filter((m) => m.status === LibraryMemberStatus.ACTIVE)
                    .map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.membership_number} ({m.member_category})
                      </option>
                    ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Issuing Branch</label>
                  <select
                    required
                    value={checkoutForm.checkout_library_id}
                    onChange={(e) => setCheckoutForm({ ...checkoutForm, checkout_library_id: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    <option value="">Select Branch...</option>
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Loan Duration (Days)</label>
                  <input
                    type="number"
                    value={checkoutForm.loan_duration_days}
                    onChange={(e) => setCheckoutForm({ ...checkoutForm, loan_duration_days: Number(e.target.value) })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCheckoutModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Complete Checkout
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 5. Return Check-In Modal */}
      {isReturnModalOpen && selectedLoanForReturn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                Check In / Return Copy
              </h3>
              <button onClick={() => setIsReturnModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleReturnLoan} className="space-y-3.5 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-slate-300">
                Loan ID: {selectedLoanForReturn.id}
                <div className="text-slate-500 text-[11px] mt-0.5">
                  Due: {new Date(selectedLoanForReturn.due_date).toLocaleDateString()}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Receiving Branch</label>
                  <select
                    required
                    value={returnForm.returned_to_library_id}
                    onChange={(e) => setReturnForm({ ...returnForm, returned_to_library_id: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    <option value="">Select Branch...</option>
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Observed Condition</label>
                  <select
                    value={returnForm.observed_condition}
                    onChange={(e) => setReturnForm({ ...returnForm, observed_condition: e.target.value as any })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    {Object.values(LibraryCopyCondition).map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Assess Additional Damage Fine ($)</label>
                <input
                  type="number"
                  step="0.01"
                  value={returnForm.assess_damage_fine}
                  onChange={(e) => setReturnForm({ ...returnForm, assess_damage_fine: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsReturnModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold"
                >
                  Confirm Return
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 6. Waive Fine Modal */}
      {isWaiveFineModalOpen && selectedFineForWaiver && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Coins className="h-5 w-5 text-indigo-400" />
                Authorize Fine Waiver
              </h3>
              <button onClick={() => setIsWaiveFineModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleWaiveFine} className="space-y-3.5 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <div className="text-slate-400">Assessed Fine: ${Number(selectedFineForWaiver.base_amount).toFixed(2)}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">Category: {selectedFineForWaiver.fine_category}</div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Waive Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={waiverForm.waived_amount}
                  onChange={(e) => setWaiverForm({ ...waiverForm, waived_amount: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Official Justification Reason</label>
                <textarea
                  required
                  rows={3}
                  value={waiverForm.waiver_reason}
                  onChange={(e) => setWaiverForm({ ...waiverForm, waiver_reason: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsWaiveFineModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Confirm Waiver
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 7. New Acquisition Request Modal */}
      {isNewAcquisitionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShoppingCart className="h-5 w-5 text-indigo-400" />
                Submit Resource Purchase / Acquisition Request
              </h3>
              <button onClick={() => setIsNewAcquisitionModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleCreateAcquisition} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Book / Material Title</label>
                <input
                  type="text"
                  required
                  value={acquisitionForm.title}
                  onChange={(e) => setAcquisitionForm({ ...acquisitionForm, title: e.target.value })}
                  placeholder="Designing Data-Intensive Applications"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Author</label>
                  <input
                    type="text"
                    value={acquisitionForm.author}
                    onChange={(e) => setAcquisitionForm({ ...acquisitionForm, author: e.target.value })}
                    placeholder="Martin Kleppmann"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">ISBN</label>
                  <input
                    type="text"
                    value={acquisitionForm.isbn}
                    onChange={(e) => setAcquisitionForm({ ...acquisitionForm, isbn: e.target.value })}
                    placeholder="978-1449373320"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    value={acquisitionForm.quantity_requested}
                    onChange={(e) => setAcquisitionForm({ ...acquisitionForm, quantity_requested: Number(e.target.value) })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Estimated Cost ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={acquisitionForm.estimated_total_cost}
                    onChange={(e) => setAcquisitionForm({ ...acquisitionForm, estimated_total_cost: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewAcquisitionModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Submit Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 8. New Subscription Modal */}
      {isNewSubscriptionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="h-5 w-5 text-indigo-400" />
                Register Journal / Periodical Subscription
              </h3>
              <button onClick={() => setIsNewSubscriptionModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleCreateSubscription} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Publication Title</label>
                <input
                  type="text"
                  required
                  placeholder="IEEE Software Magazine"
                  value={subscriptionForm.publication_title}
                  onChange={(e) => setSubscriptionForm({ ...subscriptionForm, publication_title: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Publisher / Vendor</label>
                  <input
                    type="text"
                    required
                    placeholder="IEEE Computer Society"
                    value={subscriptionForm.publisher_or_vendor}
                    onChange={(e) => setSubscriptionForm({ ...subscriptionForm, publisher_or_vendor: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Subscription Type</label>
                  <select
                    value={subscriptionForm.subscription_type}
                    onChange={(e) => setSubscriptionForm({ ...subscriptionForm, subscription_type: e.target.value as any })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    {Object.values(LibrarySubscriptionType).map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Annual Cost ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={subscriptionForm.annual_subscription_cost}
                    onChange={(e) => setSubscriptionForm({ ...subscriptionForm, annual_subscription_cost: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Digital Access Portal URL</label>
                  <input
                    type="text"
                    value={subscriptionForm.digital_access_portal_url}
                    onChange={(e) => setSubscriptionForm({ ...subscriptionForm, digital_access_portal_url: e.target.value })}
                    placeholder="https://..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewSubscriptionModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Save Subscription
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 9. Initiate Stock Audit Modal */}
      {isNewAuditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ClipboardCheck className="h-5 w-5 text-indigo-400" />
                Initiate Physical Stock Verification Audit
              </h3>
              <button onClick={() => setIsNewAuditModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleStartAudit} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Audit Code</label>
                <input
                  type="text"
                  required
                  value={auditForm.audit_code}
                  onChange={(e) => setAuditForm({ ...auditForm, audit_code: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Audit Title / Name</label>
                <input
                  type="text"
                  required
                  value={auditForm.audit_name}
                  onChange={(e) => setAuditForm({ ...auditForm, audit_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Audited Branch</label>
                <select
                  required
                  value={auditForm.library_id}
                  onChange={(e) => setAuditForm({ ...auditForm, library_id: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                >
                  <option value="">Select Branch...</option>
                  {branches.map((b) => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Scope & Stack Notes</label>
                <textarea
                  rows={3}
                  value={auditForm.scope_notes}
                  onChange={(e) => setAuditForm({ ...auditForm, scope_notes: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewAuditModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Start Verification
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 10. Audit Scan Accession Modal */}
      {isAuditScanModalOpen && selectedAuditForScan && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ClipboardCheck className="h-5 w-5 text-indigo-400" />
                Record Barcode / RFID Physical Scan
              </h3>
              <button onClick={() => setIsAuditScanModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleRecordAuditScan} className="space-y-3.5 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <div className="text-slate-200 font-semibold">{selectedAuditForScan.title}</div>
                <div className="text-slate-500 text-[11px] font-mono mt-0.5">{selectedAuditForScan.audit_code}</div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Scanned Accession Number</label>
                <input
                  type="text"
                  required
                  autoFocus
                  placeholder="Scan barcode or type ACC-2026-..."
                  value={auditScanForm.scanned_accession_number}
                  onChange={(e) => setAuditScanForm({ ...auditScanForm, scanned_accession_number: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-mono"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Observed Condition</label>
                  <select
                    value={auditScanForm.observed_condition}
                    onChange={(e) => setAuditScanForm({ ...auditScanForm, observed_condition: e.target.value as any })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    {Object.values(LibraryCopyCondition).map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Shelf Location</label>
                  <input
                    type="text"
                    value={auditScanForm.scan_location}
                    onChange={(e) => setAuditScanForm({ ...auditScanForm, scan_location: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAuditScanModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Done Scanning
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Record Item Scan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
