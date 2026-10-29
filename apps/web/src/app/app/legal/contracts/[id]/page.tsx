"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  ExternalLink,
  FileCheck,
  FileEdit,
  FileSpreadsheet,
  FileText,
  Gavel,
  History,
  Lock,
  Plus,
  RefreshCw,
  Scale,
  Send,
  Shield,
  ShieldAlert,
  User,
  X,
  XCircle,
} from "lucide-react";
import { LegalNav } from "@/components/legal/legal-nav";
import { legalService } from "@/services/legal.service";
import {
  canTransitionContract,
  formatCurrency,
  formatLegalDate,
  getConfidentialityBadge,
  getContractStatusBadge,
  getExecutionMethodLabel,
  getObligationStatusBadge,
} from "@/services/legal-calculator";
import {
  ContractAmendment,
  ContractAmendmentCreateInput,
  ContractExecutionConfirmInput,
  ContractObligation,
  ContractObligationCreateInput,
  ContractStatus,
  ContractTransitionInput,
  ExecutionMethod,
  InstitutionalContract,
  ObligationCategory,
} from "@/types/legal";

const LIFECYCLE_STEPS: ContractStatus[] = [
  "DRAFT",
  "INTERNAL_REVIEW",
  "DEPARTMENT_APPROVAL",
  "LEGAL_REVIEW",
  "AUTHORIZED_APPROVAL",
  "READY_FOR_EXECUTION",
  "EXECUTED",
  "ACTIVE",
];

export default function ContractDetailsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const router = useRouter();
  const contractId = resolvedParams.id;

  const [contract, setContract] = useState<InstitutionalContract | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "obligations" | "amendments" | "audit">("overview");

  // Modals state
  const [isTransitionOpen, setIsTransitionOpen] = useState(false);
  const [isExecuteOpen, setIsExecuteOpen] = useState(false);
  const [isObligationOpen, setIsObligationOpen] = useState(false);
  const [isAmendmentOpen, setIsAmendmentOpen] = useState(false);

  // Transition form
  const [nextStatus, setNextStatus] = useState<ContractStatus>("INTERNAL_REVIEW");
  const [transitionComments, setTransitionComments] = useState("");
  const [transitionReviewer, setTransitionReviewer] = useState("Adv. Sarah Jenkins (Legal Counsel)");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Execution form
  const [executionMethod, setExecutionMethod] = useState<ExecutionMethod>("EXTERNAL_DIGITAL_SUITE_CONFIRMED");
  const [signatoryName, setSignatoryName] = useState("Prof. Arthur Vance (VP Academic & Provost)");
  const [signatoryTitle, setSignatoryTitle] = useState("Authorized Institutional Signatory");
  const [counterpartySignatory, setCounterpartySignatory] = useState("");
  const [counterpartySignedDate, setCounterpartySignedDate] = useState(new Date().toISOString().split("T")[0]);
  const [certificateRef, setCertificateRef] = useState("DOCUSIGN-ENV-90214-X");
  const [executionNotes, setExecutionNotes] = useState("Wet/digital signatures verified against counterparty power of attorney.");

  // Obligation form
  const [oblTitle, setOblTitle] = useState("");
  const [oblCategory, setOblCategory] = useState<ObligationCategory>("DELIVERABLE");
  const [oblDueDate, setOblDueDate] = useState("");
  const [oblRequiredEvidence, setOblRequiredEvidence] = useState("");

  // Amendment form
  const [amendNumber, setAmendNumber] = useState(1);
  const [amendSummary, setAmendSummary] = useState("");
  const [amendEffectiveDate, setAmendEffectiveDate] = useState(new Date().toISOString().split("T")[0]);
  const [amendValueDelta, setAmendValueDelta] = useState<number>(0);

  useEffect(() => {
    loadContract();
  }, [contractId]);

  async function loadContract() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await legalService.getContract(contractId);
      setContract(data);
      if (data.amendments?.length) {
        setAmendNumber(data.amendments.length + 1);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load contract details");
    } finally {
      setLoading(false);
    }
  }

  async function handleTransitionSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!contract) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: ContractTransitionInput = {
        to_status: nextStatus,
        comments: transitionComments,
        reviewer_name: transitionReviewer,
      };
      const updated = await legalService.transitionContract(contract.id, input);
      setContract(updated);
      setIsTransitionOpen(false);
      setTransitionComments("");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to advance contract lifecycle");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleExecutionSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!contract) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: ContractExecutionConfirmInput = {
        execution_method: executionMethod,
        signatory_name: signatoryName,
        signatory_title: signatoryTitle,
        counterparty_signatory: counterpartySignatory || contract.counterparty_name,
        counterparty_signed_date: counterpartySignedDate,
        certificate_reference: certificateRef,
        notes: executionNotes,
      };
      const updated = await legalService.confirmExecution(contract.id, input);
      setContract(updated);
      setIsExecuteOpen(false);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record contract execution");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleObligationSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!contract) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: ContractObligationCreateInput = {
        contract_id: contract.id,
        title: oblTitle,
        category: oblCategory,
        due_date: oblDueDate,
        required_evidence: oblRequiredEvidence,
        responsible_owner_id: contract.internal_owner_id,
      };
      await legalService.createObligation(input);
      setIsObligationOpen(false);
      setOblTitle("");
      setOblRequiredEvidence("");
      // Refresh contract
      await loadContract();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to add obligation");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleAmendmentSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!contract) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: ContractAmendmentCreateInput = {
        amendment_number: amendNumber,
        summary: amendSummary,
        effective_date: amendEffectiveDate,
        financial_value_delta: amendValueDelta,
      };
      await legalService.addAmendment(contract.id, input);
      setIsAmendmentOpen(false);
      setAmendSummary("");
      await loadContract();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record amendment");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        <LegalNav />
        <div className="max-w-7xl mx-auto px-6 py-20 text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-indigo-600 mb-4" />
          <p className="text-sm text-slate-500">Loading institutional contract workspace...</p>
        </div>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        <LegalNav />
        <div className="max-w-4xl mx-auto px-6 py-16 text-center">
          <XCircle className="h-12 w-12 text-rose-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Contract Record Not Found</h2>
          <p className="text-sm text-slate-500 mt-2">The contract could not be retrieved or you lack permission clearance.</p>
          <Link
            href="/app/legal/contracts"
            className="inline-flex items-center gap-2 mt-6 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
          >
            <ArrowLeft className="h-4 w-4" /> Return to Contracts Register
          </Link>
        </div>
      </div>
    );
  }

  const currentStepIdx = LIFECYCLE_STEPS.indexOf(contract.status);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <LegalNav />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Breadcrumb & Navigation */}
        <div className="flex items-center justify-between">
          <Link
            href="/app/legal/contracts"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-900 dark:hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Contracts Register
          </Link>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded-full font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              {contract.contract_number}
            </span>
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-medium ${getConfidentialityBadge(
                contract.confidentiality_level
              )}`}
            >
              {contract.confidentiality_level}
            </span>
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-medium ${getContractStatusBadge(
                contract.status
              )}`}
            >
              {contract.status.replace(/_/g, " ")}
            </span>
          </div>
        </div>

        {/* Header Hero Card */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
                  <FileText className="h-6 w-6" />
                </span>
                <div>
                  <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{contract.title}</h1>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Counterparty: <strong className="text-slate-700 dark:text-slate-200">{contract.counterparty_name}</strong> • Category: {contract.category.replace(/_/g, " ")}
                  </p>
                </div>
              </div>
              {contract.purpose && (
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 max-w-3xl">
                  {contract.purpose}
                </p>
              )}
            </div>

            {/* Lifecycle Action Buttons */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => setIsTransitionOpen(true)}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
              >
                <Send className="h-4 w-4" /> Advance Lifecycle
              </button>

              {(contract.status === "READY_FOR_EXECUTION" || contract.status === "AUTHORIZED_APPROVAL") && (
                <button
                  onClick={() => setIsExecuteOpen(true)}
                  className="px-4 py-2.5 rounded-xl bg-emerald-600 text-white font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm flex items-center gap-2"
                >
                  <FileCheck className="h-4 w-4" /> Record Execution
                </button>
              )}

              <button
                onClick={() => setIsObligationOpen(true)}
                className="px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-sm hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
              >
                <Plus className="h-4 w-4" /> Add Obligation
              </button>

              <button
                onClick={() => setIsAmendmentOpen(true)}
                className="px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-sm hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
              >
                <FileEdit className="h-4 w-4" /> Add Amendment
              </button>
            </div>
          </div>

          {/* Lifecycle Stepper */}
          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Contract Lifecycle Progression
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
              {LIFECYCLE_STEPS.map((step, idx) => {
                const isPassed = currentStepIdx >= idx;
                const isCurrent = contract.status === step;

                return (
                  <div
                    key={step}
                    className={`p-2.5 rounded-lg border text-center transition-all ${
                      isCurrent
                        ? "bg-indigo-50 dark:bg-indigo-950/60 border-indigo-400 dark:border-indigo-600 text-indigo-700 dark:text-indigo-300 shadow-sm"
                        : isPassed
                        ? "bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400"
                        : "bg-transparent border-dashed border-slate-200 dark:border-slate-800 text-slate-400 opacity-60"
                    }`}
                  >
                    <div className="text-[10px] font-bold tracking-tight">STEP {idx + 1}</div>
                    <div className="text-xs font-semibold truncate mt-0.5">
                      {step.replace(/_/g, " ")}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 gap-6">
          <button
            onClick={() => setActiveTab("overview")}
            className={`pb-3 text-sm font-semibold transition-colors border-b-2 flex items-center gap-2 ${
              activeTab === "overview"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <FileText className="h-4 w-4" /> Overview & Legal Terms
          </button>
          <button
            onClick={() => setActiveTab("obligations")}
            className={`pb-3 text-sm font-semibold transition-colors border-b-2 flex items-center gap-2 ${
              activeTab === "obligations"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <CheckCircle2 className="h-4 w-4" /> Obligations & Deliverables
            <span className="px-2 py-0.5 text-xs rounded-full bg-slate-100 dark:bg-slate-800">
              {contract.obligations?.length || 0}
            </span>
          </button>
          <button
            onClick={() => setActiveTab("amendments")}
            className={`pb-3 text-sm font-semibold transition-colors border-b-2 flex items-center gap-2 ${
              activeTab === "amendments"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <FileSpreadsheet className="h-4 w-4" /> Amendments & Addenda
            <span className="px-2 py-0.5 text-xs rounded-full bg-slate-100 dark:bg-slate-800">
              {contract.amendments?.length || 0}
            </span>
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`pb-3 text-sm font-semibold transition-colors border-b-2 flex items-center gap-2 ${
              activeTab === "audit"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <History className="h-4 w-4" /> Approval & Audit Chain
            <span className="px-2 py-0.5 text-xs rounded-full bg-slate-100 dark:bg-slate-800">
              {contract.approval_chain_json?.length || 0}
            </span>
          </button>
        </div>

        {/* Tab 1: Overview & Legal Terms */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Scale className="h-5 w-5 text-indigo-600" /> Contract Term & Financial Parameters
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                    <span className="text-xs text-slate-500 block">Total Financial Value</span>
                    <strong className="text-lg font-bold text-slate-900 dark:text-white">
                      {formatCurrency(contract.financial_value, contract.currency)}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                    <span className="text-xs text-slate-500 block">Governing Law & Jurisdiction</span>
                    <strong className="text-sm font-semibold text-slate-900 dark:text-white">
                      {contract.governing_law || "Not Specified (Default Institutional Jurisdiction)"}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                    <span className="text-xs text-slate-500 block">Effective Date</span>
                    <strong className="text-sm font-semibold text-slate-900 dark:text-white">
                      {formatLegalDate(contract.effective_date)}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                    <span className="text-xs text-slate-500 block">Expiration Date</span>
                    <strong className="text-sm font-semibold text-slate-900 dark:text-white">
                      {formatLegalDate(contract.expiration_date)}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                    <span className="text-xs text-slate-500 block">Auto-Renew Policy</span>
                    <strong className="text-sm font-semibold text-slate-900 dark:text-white">
                      {contract.auto_renew ? `Yes (${contract.renewal_notice_days || 30} days notice)` : "Manual Expiration"}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                    <span className="text-xs text-slate-500 block">Termination Notice Period</span>
                    <strong className="text-sm font-semibold text-slate-900 dark:text-white">
                      {contract.termination_notice_days ? `${contract.termination_notice_days} Calendar Days` : "Standard Clause"}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Execution Record Banner */}
              {contract.executed_at && (
                <div className="p-6 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 space-y-3">
                  <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-bold text-sm">
                    <FileCheck className="h-5 w-5 text-emerald-600" />
                    Legally Executed Contract Record
                  </div>
                  <p className="text-xs text-emerald-900 dark:text-emerald-200">
                    Execution confirmed via <strong>{getExecutionMethodLabel(contract.execution_method)}</strong> on{" "}
                    <strong>{formatLegalDate(contract.executed_at)}</strong>.
                  </p>
                </div>
              )}
            </div>

            {/* Right Column: Counterparty & Responsible Owner */}
            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <User className="h-5 w-5 text-indigo-600" /> Counterparty Details
                </h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-xs text-slate-500 block">Organization Name</span>
                    <strong className="text-slate-900 dark:text-white">{contract.counterparty_name}</strong>
                  </div>
                  {contract.counterparty_contact_json && (
                    <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 text-xs space-y-1">
                      <div>Contact: {contract.counterparty_contact_json.contact || "Primary Counsel / Representative"}</div>
                      <div>Email: {contract.counterparty_contact_json.email || "contracts@" + contract.counterparty_name.toLowerCase().replace(/\s+/g, "") + ".com"}</div>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Shield className="h-5 w-5 text-indigo-600" /> Institutional Stewardship
                </h3>
                <div className="text-xs text-slate-600 dark:text-slate-400 space-y-2">
                  <p>
                    <strong>Responsible Department:</strong> {contract.department_id || "Institutional Office / IT / Academic Affairs"}
                  </p>
                  <p>
                    <strong>Internal Owner ID:</strong> {contract.internal_owner_id}
                  </p>
                  <p>
                    <strong>Campus Scope:</strong> {contract.campus_id || "All Institutional Campuses (Multi-Campus Master Agreement)"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Obligations & Deliverables */}
        {activeTab === "obligations" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">Contractual Obligations & Deliverables</h3>
                <p className="text-xs text-slate-500">
                  Track recurring reporting milestones, SLA commitments, warranty proofs, and compliance requirements.
                </p>
              </div>
              <button
                onClick={() => setIsObligationOpen(true)}
                className="px-3.5 py-2 rounded-lg bg-indigo-600 text-white font-medium text-xs hover:bg-indigo-700 transition-colors flex items-center gap-2"
              >
                <Plus className="h-3.5 w-3.5" /> Add New Obligation
              </button>
            </div>

            {contract.obligations && contract.obligations.length > 0 ? (
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="px-6 py-3">Obligation</th>
                      <th className="px-6 py-3">Category</th>
                      <th className="px-6 py-3">Due Date</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3">Escalation</th>
                      <th className="px-6 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {contract.obligations.map((obl) => (
                      <tr key={obl.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                        <td className="px-6 py-4">
                          <strong className="block text-slate-900 dark:text-white">{obl.title}</strong>
                          {(obl.required_evidence || obl.evidence_document_id) && (
                            <span className="text-xs text-slate-400">Required: {obl.required_evidence || obl.evidence_document_id}</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-xs font-medium text-slate-600 dark:text-slate-300">
                          {obl.category || obl.obligation_type}
                        </td>
                        <td className="px-6 py-4 text-xs font-mono">
                          {formatLegalDate(obl.due_date)}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`text-xs px-2.5 py-1 rounded-full font-medium ${getObligationStatusBadge(
                              obl.status
                            )}`}
                          >
                            {obl.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs">
                          {obl.escalation_level > 0 ? (
                            <span className="text-rose-600 font-bold flex items-center gap-1">
                              <AlertTriangle className="h-3.5 w-3.5" /> Level {obl.escalation_level}
                            </span>
                          ) : (
                            <span className="text-slate-400">Standard</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <Link
                            href="/app/legal/obligations"
                            className="text-xs font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
                          >
                            Manage in Register →
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800">
                <CheckCircle2 className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No Commitments Recorded</p>
                <p className="text-xs text-slate-500 mt-1">Register deliverables, audit checkpoints, and renewal obligations.</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Amendments & Addenda */}
        {activeTab === "amendments" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">Contract Amendments & Addenda</h3>
                <p className="text-xs text-slate-500">
                  Strict version-controlled record of formal amendments, scope expansions, and financial adjustments.
                </p>
              </div>
              <button
                onClick={() => setIsAmendmentOpen(true)}
                className="px-3.5 py-2 rounded-lg bg-indigo-600 text-white font-medium text-xs hover:bg-indigo-700 transition-colors flex items-center gap-2"
              >
                <Plus className="h-3.5 w-3.5" /> Record Amendment
              </button>
            </div>

            {contract.amendments && contract.amendments.length > 0 ? (
              <div className="space-y-3">
                {contract.amendments.map((amend) => (
                  <div
                    key={amend.id}
                    className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                          Amendment #{amend.amendment_number}
                        </span>
                        <span className="text-xs text-slate-400">
                          Effective: {formatLegalDate(amend.effective_date)}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{amend.summary || amend.title}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-slate-500 block">Financial Adjustment</span>
                      <strong className={`text-sm font-mono ${(amend.financial_value_delta ?? amend.financial_value_adjustment ?? 0) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                        {(amend.financial_value_delta ?? amend.financial_value_adjustment ?? 0) >= 0 ? "+" : ""}
                        {formatCurrency(amend.financial_value_delta ?? amend.financial_value_adjustment ?? 0, contract.currency)}
                      </strong>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800">
                <FileSpreadsheet className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No Amendments Recorded</p>
                <p className="text-xs text-slate-500 mt-1">Contract remains under its original baseline execution terms.</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Approval & Audit Chain */}
        {activeTab === "audit" && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Authorized Approval & Audit Chain</h3>
              <p className="text-xs text-slate-500">
                Immutable institutional record of department, legal counsel, and executive decisions.
              </p>
            </div>

            {contract.approval_chain_json && contract.approval_chain_json.length > 0 ? (
              <div className="relative pl-6 border-l-2 border-indigo-200 dark:border-indigo-900 space-y-6 my-4">
                {contract.approval_chain_json.map((step: any, idx: number) => (
                  <div key={idx} className="relative group">
                    <div className="absolute -left-[31px] top-1 h-4 w-4 rounded-full bg-indigo-600 border-4 border-white dark:border-slate-950" />
                    <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
                      <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                        <span className="font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                          {step.step?.replace(/_/g, " ") || `Decision Step ${idx + 1}`}
                        </span>
                        <span>{formatLegalDate(step.decided_at || step.timestamp)}</span>
                      </div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">
                        Reviewer: {step.reviewer_name || "Institutional Signatory"}
                      </p>
                      {step.comments && (
                        <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
                          "{step.comments}"
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800">
                <History className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No Review Decisions Recorded</p>
                <p className="text-xs text-slate-500 mt-1">Lifecycle transition decisions will be recorded here.</p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* MODAL 1: Advance Contract Lifecycle */}
      {isTransitionOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Send className="h-5 w-5 text-indigo-600" /> Advance Lifecycle Transition
              </h3>
              <button
                onClick={() => setIsTransitionOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleTransitionSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Target Contract Status
                </label>
                <select
                  value={nextStatus}
                  onChange={(e) => setNextStatus(e.target.value as ContractStatus)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                >
                  <option value="INTERNAL_REVIEW">INTERNAL_REVIEW — Primary Department Review</option>
                  <option value="DEPARTMENT_APPROVAL">DEPARTMENT_APPROVAL — Dean / Unit Head Sign-off</option>
                  <option value="LEGAL_REVIEW">LEGAL_REVIEW — University Counsel Compliance Check</option>
                  <option value="AUTHORIZED_APPROVAL">AUTHORIZED_APPROVAL — Provost / VP Executive Sign-off</option>
                  <option value="READY_FOR_EXECUTION">READY_FOR_EXECUTION — Counterparty Signing Cleared</option>
                  <option value="ACTIVE">ACTIVE — Executed and In Force</option>
                  <option value="ON_HOLD">ON_HOLD — Pending External Dispute / Negotiation</option>
                  <option value="REJECTED">REJECTED — Denied by Reviewer</option>
                  <option value="TERMINATED">TERMINATED — Early Formal Termination</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Reviewer Identity
                </label>
                <input
                  type="text"
                  value={transitionReviewer}
                  onChange={(e) => setTransitionReviewer(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Review / Transition Comments
                </label>
                <textarea
                  rows={3}
                  value={transitionComments}
                  onChange={(e) => setTransitionComments(e.target.value)}
                  placeholder="Record justification, review notes, or stipulations..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              {errorMsg && (
                <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300 text-xs">
                  {errorMsg}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsTransitionOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  {isSubmitting ? "Submitting..." : "Confirm Transition"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Record Contract Execution */}
      {isExecuteOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-emerald-600" /> Record External Execution
              </h3>
              <button
                onClick={() => setIsExecuteOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                <strong>Compliance Policy:</strong> CampusOS records verified execution without claiming to be an authorized electronic signing authority. Ensure counterparty credentials match institutional records.
              </span>
            </div>

            <form onSubmit={handleExecutionSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Verified Execution Method
                </label>
                <select
                  value={executionMethod}
                  onChange={(e) => setExecutionMethod(e.target.value as ExecutionMethod)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                >
                  <option value="EXTERNAL_DIGITAL_SUITE_CONFIRMED">DocuSign / Adobe Sign Audit Certificate</option>
                  <option value="WET_SIGNATURE_CONFIRMED">Physical Wet Signature (Countersigned Scan)</option>
                  <option value="BOARD_RESOLUTION_CONFIRMED">Governing Board Seal & Resolution</option>
                  <option value="HYBRID_CONFIRMED">Hybrid Counterpart Execution</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Internal Signatory
                  </label>
                  <input
                    type="text"
                    value={signatoryName}
                    onChange={(e) => setSignatoryName(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Signatory Title
                  </label>
                  <input
                    type="text"
                    value={signatoryTitle}
                    onChange={(e) => setSignatoryTitle(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Counterparty Signatory
                  </label>
                  <input
                    type="text"
                    value={counterpartySignatory}
                    placeholder={contract.counterparty_name}
                    onChange={(e) => setCounterpartySignatory(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Counterparty Signed Date
                  </label>
                  <input
                    type="date"
                    value={counterpartySignedDate}
                    onChange={(e) => setCounterpartySignedDate(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Certificate / Document Reference
                </label>
                <input
                  type="text"
                  value={certificateRef}
                  onChange={(e) => setCertificateRef(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsExecuteOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700"
                >
                  {isSubmitting ? "Recording..." : "Confirm Execution Record"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Add Obligation */}
      {isObligationOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-indigo-600" /> Register Contract Obligation
              </h3>
              <button
                onClick={() => setIsObligationOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleObligationSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Obligation Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Annual SOC 2 Type II Security Compliance Audit"
                  value={oblTitle}
                  onChange={(e) => setOblTitle(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Obligation Category
                  </label>
                  <select
                    value={oblCategory}
                    onChange={(e) => setOblCategory(e.target.value as ObligationCategory)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="DELIVERABLE">DELIVERABLE</option>
                    <option value="REPORTING">REPORTING</option>
                    <option value="PAYMENT_MILESTONE">PAYMENT_MILESTONE</option>
                    <option value="SERVICE_COMMITMENT">SERVICE_COMMITMENT</option>
                    <option value="INSURANCE_REQUIREMENT">INSURANCE_REQUIREMENT</option>
                    <option value="RENEWAL_NOTICE">RENEWAL_NOTICE</option>
                    <option value="AUDIT_RIGHT">AUDIT_RIGHT</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Due Date
                  </label>
                  <input
                    type="date"
                    value={oblDueDate}
                    onChange={(e) => setOblDueDate(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Required Proof / Evidence
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Third-party CPA audit report and certificate of insurance."
                  value={oblRequiredEvidence}
                  onChange={(e) => setOblRequiredEvidence(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsObligationOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  {isSubmitting ? "Creating..." : "Save Obligation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: Add Amendment */}
      {isAmendmentOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <FileEdit className="h-5 w-5 text-indigo-600" /> Record Contract Amendment
              </h3>
              <button
                onClick={() => setIsAmendmentOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAmendmentSubmit} className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Amendment Number
                  </label>
                  <input
                    type="number"
                    value={amendNumber}
                    onChange={(e) => setAmendNumber(parseInt(e.target.value) || 1)}
                    required
                    min={1}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Effective Date
                  </label>
                  <input
                    type="date"
                    value={amendEffectiveDate}
                    onChange={(e) => setAmendEffectiveDate(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Amendment Summary & Scope Change
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe term adjustments, schedule modifications, or SLA modifications..."
                  value={amendSummary}
                  onChange={(e) => setAmendSummary(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Financial Value Delta ({contract.currency})
                </label>
                <input
                  type="number"
                  value={amendValueDelta}
                  onChange={(e) => setAmendValueDelta(parseFloat(e.target.value) || 0)}
                  placeholder="0.00 (negative for reductions)"
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAmendmentOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  {isSubmitting ? "Recording..." : "Save Amendment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
