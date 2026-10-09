"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  documentsService,
  documentCategoriesService,
  documentUploadService,
} from "@/services";
import {
  DocumentCategory,
  DocumentCategoryCode,
  DocumentOwnerType,
  ConfidentialityLevel,
  VerificationPriority,
} from "@campusos/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Upload,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  FileText,
  AlertCircle,
  FileCheck,
  User,
  Shield,
  Clock,
  Sparkles,
  Layers,
} from "lucide-react";

export default function DocumentUploadPage() {
  const router = useRouter();

  // Stepper state: 1: Owner -> 2: Category -> 3: Document Type -> 4: Metadata -> 5: File -> 6: Review & Submit
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [categories, setCategories] = useState<DocumentCategory[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  // Form State
  const [ownerType, setOwnerType] = useState<DocumentOwnerType>(DocumentOwnerType.STUDENT);
  const [ownerId, setOwnerId] = useState("stu-001");
  const [ownerName, setOwnerName] = useState("Aarav Patel");
  const [ownerRollNumber, setOwnerRollNumber] = useState("24CSE0101");
  const [ownerDepartment, setOwnerDepartment] = useState("Computer Science & Engineering");

  const [categoryCode, setCategoryCode] = useState<DocumentCategoryCode>(DocumentCategoryCode.IDENTITY);
  const [documentType, setDocumentType] = useState("Aadhaar Card");
  const [documentName, setDocumentName] = useState("");
  const [documentNumber, setDocumentNumber] = useState("");
  const [issuingAuthority, setIssuingAuthority] = useState("");
  const [issueDate, setIssueDate] = useState("");
  const [expiryDate, setExpiryDate] = useState("");
  const [confidentiality, setConfidentiality] = useState<ConfidentialityLevel>(ConfidentialityLevel.INTERNAL);
  const [priority, setPriority] = useState<VerificationPriority>(VerificationPriority.NORMAL);

  // File Upload Simulator State
  const [mockFile, setMockFile] = useState<{ name: string; size: number; type: string } | null>({
    name: "official_document_scan.pdf",
    size: 2.1 * 1024 * 1024,
    type: "application/pdf",
  });
  const [uploadState, setUploadState] = useState<"IDLE" | "SELECTED" | "UPLOADING" | "UPLOADED" | "FAILED">("SELECTED");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function loadCats() {
      try {
        setLoadingCategories(true);
        const res = await documentCategoriesService.listCategories();
        if (res.success && res.data) {
          setCategories(res.data);
          if (res.data.length > 0) {
            setCategoryCode(res.data[0].code);
            setDocumentType(res.data[0].applicableDocumentTypes[0] || "Standard Document");
          }
        }
      } catch (err) {
        console.error("Failed to load categories:", err);
      } finally {
        setLoadingCategories(false);
      }
    }

    loadCats();
  }, []);

  const activeCategory = categories.find((c) => c.code === categoryCode);

  const handleNext = () => {
    setValidationErrors([]);

    if (currentStep === 4) {
      // Validate metadata
      if (!documentName.trim()) {
        setValidationErrors(["Document title is required."]);
        return;
      }
      if (activeCategory?.expiryRequired && !expiryDate) {
        setValidationErrors(["Expiry date is mandatory for this document category."]);
        return;
      }
    }

    if (currentStep === 5) {
      if (!mockFile) {
        setValidationErrors(["A file must be selected for upload."]);
        return;
      }
    }

    setCurrentStep((prev) => Math.min(6, prev + 1));
  };

  const handlePrev = () => {
    setValidationErrors([]);
    setCurrentStep((prev) => Math.max(1, prev - 1));
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      setUploadState("UPLOADING");
      setUploadProgress(0);

      // Simulate step-by-step upload progress
      await documentUploadService.simulateUpload(
        mockFile || { name: "document.pdf", size: 1024 * 1024, type: "application/pdf" },
        (progress) => setUploadProgress(progress)
      );

      setUploadState("UPLOADED");

      // Commit document via service
      const res = await documentsService.uploadDocument({
        name: documentName || `${documentType} - ${ownerName}`,
        category: categoryCode,
        documentType,
        ownerType,
        ownerId,
        ownerName,
        ownerRollNumber,
        ownerDepartment,
        confidentiality,
        documentNumber,
        issuingAuthority,
        issueDate,
        expiryDate: expiryDate || undefined,
        priority,
        fileSize: mockFile ? `${(mockFile.size / (1024 * 1024)).toFixed(1)} MB` : "1.8 MB",
        fileType: mockFile?.type || "application/pdf",
      });

      if (res.success && res.data) {
        // Redirect to detail page
        router.push(`/app/documents/${res.data.id}`);
      }
    } catch (err) {
      console.error("Submission failed:", err);
      setUploadState("FAILED");
      setValidationErrors(["Failed to complete document submission. Please try again."]);
    } finally {
      setSubmitting(false);
    }
  };

  const stepsList = [
    { num: 1, title: "Owner" },
    { num: 2, title: "Category" },
    { num: 3, title: "Doc Type" },
    { num: 4, title: "Metadata" },
    { num: 5, title: "File" },
    { num: 6, title: "Review" },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/documents/my-documents"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Cancel & Return to Vault
        </Link>
        <span className="text-xs text-slate-500 font-mono">Step {currentStep} of 6</span>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-slate-100">Upload Official Document</h1>
        <p className="text-sm text-slate-400 mt-1">
          Submit official academic records, proof of identity, certificates, and credentials for institutional verification.
        </p>
      </div>

      {/* Visual Stepper */}
      <div className="grid grid-cols-6 gap-2 bg-slate-900 border border-slate-800 p-3 rounded-xl">
        {stepsList.map((step) => {
          const isDone = step.num < currentStep;
          const isCurrent = step.num === currentStep;
          return (
            <div
              key={step.num}
              className={`flex items-center gap-2 p-2 rounded-lg text-xs font-semibold transition ${
                isCurrent
                  ? "bg-blue-600 text-white shadow-sm"
                  : isDone
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                  : "text-slate-500"
              }`}
            >
              <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] border border-current">
                {isDone ? "✓" : step.num}
              </span>
              <span className="hidden sm:inline truncate">{step.title}</span>
            </div>
          );
        })}
      </div>

      {/* Validation Alert */}
      {validationErrors.length > 0 && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl space-y-1 text-xs text-rose-300">
          <div className="flex items-center gap-1.5 font-bold text-rose-400">
            <AlertCircle className="w-4 h-4" />
            Please address the following requirements:
          </div>
          {validationErrors.map((err, i) => (
            <div key={i}>• {err}</div>
          ))}
        </div>
      )}

      {/* STEP CONTAINER */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 sm:p-8 space-y-6">
        {/* STEP 1: SELECT OWNER */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <User className="w-5 h-5 text-blue-400" />
                Step 1: Specify Document Owner
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Select whether this document belongs to a student, faculty member, or institutional department.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { type: DocumentOwnerType.STUDENT, title: "Student Record", desc: "Aarav Patel (24CSE0101)" },
                { type: DocumentOwnerType.FACULTY, title: "Faculty Record", desc: "Dr. Rajesh Sharma" },
                { type: DocumentOwnerType.INSTITUTION, title: "Institutional Record", desc: "Campus Directorate" },
              ].map((opt) => (
                <div
                  key={opt.type}
                  onClick={() => setOwnerType(opt.type)}
                  className={`p-4 rounded-xl border cursor-pointer transition ${
                    ownerType === opt.type
                      ? "bg-blue-600/15 border-blue-500 text-blue-300"
                      : "bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700"
                  }`}
                >
                  <div className="font-semibold text-sm">{opt.title}</div>
                  <div className="text-xs text-slate-400 mt-1">{opt.desc}</div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-800 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Owner Full Legal Name</label>
                <Input
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Roll / Employee Number</label>
                <Input
                  value={ownerRollNumber}
                  onChange={(e) => setOwnerRollNumber(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: SELECT CATEGORY */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-400" />
                Step 2: Choose Document Category
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Select the institutional category governing this document.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {categories.map((cat) => (
                <div
                  key={cat.code}
                  onClick={() => {
                    setCategoryCode(cat.code);
                    if (cat.applicableDocumentTypes.length > 0) {
                      setDocumentType(cat.applicableDocumentTypes[0]);
                    }
                  }}
                  className={`p-3.5 rounded-xl border cursor-pointer transition ${
                    categoryCode === cat.code
                      ? "bg-blue-600/15 border-blue-500"
                      : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-slate-200">{cat.name}</span>
                    <span className="text-[10px] font-mono text-blue-400 font-bold">{cat.code}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">{cat.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STEP 3: DOCUMENT TYPE */}
        {currentStep === 3 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                Step 3: Document Type Classification
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Selected Category: <strong className="text-blue-400">{activeCategory?.name}</strong>
              </p>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-medium text-slate-400">
                Choose Specific Document Type
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {(activeCategory?.applicableDocumentTypes || ["Standard Document"]).map((type) => (
                  <div
                    key={type}
                    onClick={() => {
                      setDocumentType(type);
                      if (!documentName) setDocumentName(`${type} - ${ownerName}`);
                    }}
                    className={`p-3 rounded-lg border text-xs cursor-pointer transition ${
                      documentType === type
                        ? "bg-blue-600/20 border-blue-500 text-blue-200 font-semibold"
                        : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
                    }`}
                  >
                    {type}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: METADATA */}
        {currentStep === 4 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-blue-400" />
                Step 4: Document Metadata
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Enter identifying numbers, issue dates, and regulatory validity.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="sm:col-span-2">
                <label className="block text-slate-400 font-medium mb-1">
                  Document Title <span className="text-rose-400">*</span>
                </label>
                <Input
                  value={documentName}
                  onChange={(e) => setDocumentName(e.target.value)}
                  placeholder="e.g. Higher Secondary Consolidated Marksheet 2024"
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Document / Serial Number</label>
                <Input
                  value={documentNumber}
                  onChange={(e) => setDocumentNumber(e.target.value)}
                  placeholder="e.g. CBSE-2024-884192"
                  className="bg-slate-950 border-slate-800 text-xs font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Issuing Authority</label>
                <Input
                  value={issuingAuthority}
                  onChange={(e) => setIssuingAuthority(e.target.value)}
                  placeholder="e.g. CBSE, Anna University, State Government"
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Issue Date</label>
                <Input
                  type="date"
                  value={issueDate}
                  onChange={(e) => setIssueDate(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">
                  Expiry Date {activeCategory?.expiryRequired && <span className="text-rose-400">*</span>}
                </label>
                <Input
                  type="date"
                  value={expiryDate}
                  onChange={(e) => setExpiryDate(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Leave blank if permanent / lifetime validity
                </span>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Confidentiality Tier</label>
                <Select
                  value={confidentiality}
                  onChange={(e) => setConfidentiality(e.target.value as ConfidentialityLevel)}
                  className="bg-slate-950 border-slate-800 text-xs"
                >
                  {Object.values(ConfidentialityLevel).map((lvl) => (
                    <option key={lvl} value={lvl}>
                      {lvl}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Verification Priority</label>
                <Select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as VerificationPriority)}
                  className="bg-slate-950 border-slate-800 text-xs"
                >
                  {Object.values(VerificationPriority).map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
          </div>
        )}

        {/* STEP 5: FILE SELECTION / PLACEHOLDER */}
        {currentStep === 5 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-400" />
                Step 5: Digital File Selection
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Upload your scanned document or choose a simulated demo file.
              </p>
            </div>

            {/* Dropzone Simulation */}
            <div className="p-8 border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl bg-slate-950/60 text-center space-y-3 transition">
              <div className="p-3 bg-blue-500/10 rounded-full w-12 h-12 flex items-center justify-center mx-auto text-blue-400">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-200">
                  {mockFile ? mockFile.name : "Select a PDF or image scan"}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Supported formats: PDF, PNG, JPG, DOCX • Maximum file size: 15 MB
                </div>
              </div>

              <div className="flex items-center justify-center gap-3 pt-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs"
                  onClick={() =>
                    setMockFile({
                      name: `${documentType.toLowerCase().replace(/\s+/g, "_")}_scanned.pdf`,
                      size: 2.4 * 1024 * 1024,
                      type: "application/pdf",
                    })
                  }
                >
                  Generate Sample PDF Scan
                </Button>
              </div>
            </div>

            {mockFile && (
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <div>
                    <span className="font-semibold text-slate-200">{mockFile.name}</span>
                    <span className="text-slate-500 ml-2 font-mono">
                      {(mockFile.size / (1024 * 1024)).toFixed(1)} MB
                    </span>
                  </div>
                </div>
                <span className="text-emerald-400 font-medium">Ready for review</span>
              </div>
            )}
          </div>
        )}

        {/* STEP 6: REVIEW & SUBMIT */}
        {currentStep === 6 && (
          <div className="space-y-6">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-400" />
                Step 6: Review & Confirm Submission
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Please verify all entered particulars before submitting to the institutional review queue.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">Document Title</span>
                <span className="font-semibold text-slate-200 mt-1 block">{documentName}</span>
              </div>

              <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">Category & Type</span>
                <span className="font-semibold text-blue-400 mt-1 block">
                  {categoryCode} • {documentType}
                </span>
              </div>

              <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">Owner</span>
                <span className="font-semibold text-slate-200 mt-1 block">
                  {ownerName} ({ownerRollNumber})
                </span>
              </div>

              <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">Doc Number & Authority</span>
                <span className="font-semibold text-slate-200 mt-1 block font-mono">
                  {documentNumber || "N/A"} ({issuingAuthority || "N/A"})
                </span>
              </div>

              <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">Validity Range</span>
                <span className="font-semibold text-slate-200 mt-1 block">
                  {issueDate || "N/A"} to {expiryDate || "Permanent"}
                </span>
              </div>

              <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">File Asset</span>
                <span className="font-semibold text-slate-200 mt-1 block">
                  {mockFile?.name} ({(mockFile?.size ? mockFile.size / (1024 * 1024) : 1).toFixed(1)} MB)
                </span>
              </div>
            </div>

            {/* Progress Bar when uploading */}
            {uploadState === "UPLOADING" && (
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between text-xs text-slate-300">
                  <span className="flex items-center gap-1.5 text-blue-400">
                    <Clock className="w-3.5 h-3.5 animate-spin" />
                    Uploading and indexing document into Vault...
                  </span>
                  <span className="font-mono font-bold">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-200"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Stepper Navigation Buttons */}
        <div className="flex items-center justify-between pt-6 border-t border-slate-800">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handlePrev}
            disabled={currentStep === 1 || submitting}
            className="text-xs gap-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Previous Step
          </Button>

          {currentStep < 6 ? (
            <Button
              type="button"
              size="sm"
              onClick={handleNext}
              className="text-xs gap-1 bg-blue-600 hover:bg-blue-700"
            >
              Continue
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          ) : (
            <Button
              type="button"
              size="sm"
              disabled={submitting}
              onClick={handleSubmit}
              className="text-xs gap-1.5 bg-emerald-600 hover:bg-emerald-700 font-semibold"
            >
              <Upload className="w-4 h-4" />
              {submitting ? "Submitting Document..." : "Submit to Verification Desk"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
