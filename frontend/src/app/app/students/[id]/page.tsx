"use client";

import React, { use, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { studentsService } from "@/services/students.service";
import { StudentComprehensiveDetail } from "@/types/domain";
import {
  GuardianRecord,
  PersonDocument,
  AcademicMilestone,
  DocumentCategory,
  StudentStatus,
  GuardianRelationType,
  MilestoneCategory,
} from "@/types/people";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Edit,
  Download,
  FileText,
  Upload,
  Plus,
  Trash2,
  ExternalLink,
} from "lucide-react";

export default function Student360ProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const studentId = resolvedParams.id;
  const { showToast } = useToast();
  const { activePersona } = useAuth();

  // Role permissions
  const canManageLifecycle =
    activePersona.role === "ADMIN" || activePersona.role === "HOD";
  const canVerifyDocs =
    activePersona.role === "ADMIN" || activePersona.role === "HOD";
  const canAddMilestones =
    activePersona.role === "ADMIN" ||
    activePersona.role === "HOD" ||
    activePersona.role === "FACULTY";

  const [student, setStudent] = useState<StudentComprehensiveDetail | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // Lifecycle status modal
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [newStatus, setNewStatus] =
    useState<StudentComprehensiveDetail["status"]>("ACTIVE");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  // Guardian Management modal
  const [guardianModalOpen, setGuardianModalOpen] = useState(false);
  const [guardianForm, setGuardianForm] = useState<Partial<GuardianRecord>>({
    name: "",
    relation: "GUARDIAN",
    relationLabel: "Local Guardian",
    phone: "",
    email: "",
    occupation: "",
    isPrimary: false,
    isEmergencyContact: true,
  });

  // Document Upload modal
  const [uploadDocModalOpen, setUploadDocModalOpen] = useState(false);
  const [docCategory, setDocCategory] = useState<DocumentCategory>("ACADEMIC");
  const [docName, setDocName] = useState("");
  const [docFileSize, setDocFileSize] = useState("1.5 MB");

  // Document Preview modal
  const [previewDoc, setPreviewDoc] = useState<PersonDocument | null>(null);

  // Milestone modal
  const [milestoneModalOpen, setMilestoneModalOpen] = useState(false);
  const [milestoneTitle, setMilestoneTitle] = useState("");
  const [milestoneDesc, setMilestoneDesc] = useState("");
  const [milestoneCategory, setMilestoneCategory] =
    useState<AcademicMilestone["category"]>("ACHIEVEMENT");
  const [milestoneSemester, setMilestoneSemester] = useState("5");

  const loadStudent = useCallback(async () => {
    setLoading(true);
    try {
      const res = await studentsService.getById(studentId);
      if (res.data) {
        setStudent(res.data);
        setNewStatus(res.data.status);
      }
    } catch {
      showToast({
        type: "error",
        title: "Record Not Found",
        message: `Failed to load canonical profile for ${studentId}.`,
      });
    } finally {
      setLoading(false);
    }
  }, [studentId, showToast]);

  useEffect(() => {
    loadStudent();
  }, [loadStudent]);

  // Update Status
  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!student) return;
    setIsUpdatingStatus(true);
    try {
      await studentsService.update(student.id, { status: newStatus });
      showToast({
        type: "success",
        title: "Lifecycle Transition",
        message: `Student status updated to ${newStatus}.`,
      });
      setStatusModalOpen(false);
      loadStudent();
    } catch {
      showToast({
        type: "error",
        title: "Update Failed",
        message: "Unable to record lifecycle transition.",
      });
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  // Add Guardian
  const handleAddGuardian = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!student) return;
    try {
      await studentsService.addGuardian(student.id, guardianForm);
      showToast({
        type: "success",
        title: "Guardian Relationship Added",
        message: `${guardianForm.name} linked as official guardian.`,
      });
      setGuardianModalOpen(false);
      setGuardianForm({
        name: "",
        relation: "GUARDIAN",
        relationLabel: "Local Guardian",
        phone: "",
        email: "",
        occupation: "",
        isPrimary: false,
        isEmergencyContact: true,
      });
      loadStudent();
    } catch {
      showToast({
        type: "error",
        title: "Action Failed",
        message: "Could not link guardian.",
      });
    }
  };

  // Remove Guardian
  const handleDeleteGuardian = async (guardianId: string) => {
    if (!student) return;
    await studentsService.deleteGuardian(student.id, guardianId);
    showToast({
      type: "info",
      title: "Guardian Removed",
      message: "Relationship record removed from profile.",
    });
    loadStudent();
  };

  // Upload Document
  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!student) return;
    try {
      await studentsService.uploadDocument(student.id, {
        name: docName,
        category: docCategory,
        fileSize: docFileSize,
        uploadedBy: "Registrar Verification Cell",
      });
      showToast({
        type: "success",
        title: "Document Vault Updated",
        message: `${docName} uploaded for scrutiny.`,
      });
      setUploadDocModalOpen(false);
      setDocName("");
      loadStudent();
    } catch {
      showToast({
        type: "error",
        title: "Upload Failed",
        message: "Failed to store document metadata.",
      });
    }
  };

  // Verify Document
  const handleVerifyDocument = async (docId: string) => {
    if (!student) return;
    await studentsService.verifyDocument(
      student.id,
      docId,
      "Admissions Directorate",
    );
    showToast({
      type: "success",
      title: "Document Verified",
      message: "Document marked with verified institutional stamp.",
    });
    loadStudent();
  };

  // Reject Document
  const handleRejectDocument = async (docId: string) => {
    if (!student) return;
    await studentsService.rejectDocument(
      student.id,
      docId,
      "Discrepancy in seal/signature.",
    );
    showToast({
      type: "warning",
      title: "Document Rejected",
      message: "Document flagged with rejection notice.",
    });
    loadStudent();
  };

  // Add Milestone
  const handleAddMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!student) return;
    try {
      await studentsService.addMilestone(student.id, {
        title: milestoneTitle,
        description: milestoneDesc,
        category: milestoneCategory,
        semester: Number(milestoneSemester),
        awardedBy: "Academic Senate",
      });
      showToast({
        type: "success",
        title: "Milestone Logged",
        message: `Milestone "${milestoneTitle}" added to student timeline.`,
      });
      setMilestoneModalOpen(false);
      setMilestoneTitle("");
      setMilestoneDesc("");
      loadStudent();
    } catch {
      showToast({
        type: "error",
        title: "Failed to Log Milestone",
        message: "Unable to add milestone event.",
      });
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center text-slate-400 font-mono text-xs">
        Loading Student 360 Master Record...
      </div>
    );
  }

  if (!student) {
    return (
      <div className="space-y-4">
        <Link href="/app/students">
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            Back to Directory
          </Button>
        </Link>
        <EmptyState
          title="Student Record Not Found"
          description={`No student master profile exists with identifier "${studentId}".`}
          actionLabel="Return to Students"
          onAction={() => (window.location.href = "/app/students")}
        />
      </div>
    );
  }

  const TABS = [
    { id: "overview", label: "Overview & Bio" },
    { id: "academic", label: "Academics & Milestones" },
    { id: "guardians", label: `Guardians (${student.guardians?.length || 1})` },
    {
      id: "documents",
      label: `Document Vault (${student.documentsVault?.length || student.documents?.length || 0})`,
    },
    { id: "timeline", label: "Lifecycle Timeline" },
    { id: "connected-modules", label: "Connected Engines" },
  ];

  const guardians = student.guardians || [];
  const documents = student.documentsVault || [];
  const milestones = student.milestones || [];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link href="/app/students">
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            Back to Student Directory
          </Button>
        </Link>
      </div>

      {/* Main Student 360 Header Banner */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 shadow-xs backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400 border border-indigo-500/20 text-2xl font-bold font-mono shrink-0">
              {student.firstName[0]}
              {student.lastName[0]}
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                  {student.firstName} {student.lastName}
                </h1>
                <Badge
                  variant={
                    student.status === "ACTIVE" ? "success" : "secondary"
                  }
                  dot
                >
                  {student.status}
                </Badge>
                <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                  {student.rollNumber}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  Ref: {student.registrationNumber}
                </span>
              </div>

              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {student.program.name} &bull; Cohort {student.academicYear}{" "}
                &bull; Semester {student.currentSemester} (Section{" "}
                {student.section})
              </p>

              <div className="mt-2.5 flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  {student.email}
                </span>
                <span className="flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5 text-slate-400" />
                  {student.phone}
                </span>
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5 text-slate-400" />
                  {student.address.city}, {student.address.state}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-center">
            {canManageLifecycle && (
              <Button
                onClick={() => setStatusModalOpen(true)}
                variant="outline"
                size="sm"
                leftIcon={<Edit className="h-3.5 w-3.5" />}
              >
                Update Status
              </Button>
            )}
            <Button
              onClick={() => setActiveTab("documents")}
              variant="primary"
              size="sm"
              leftIcon={<FileText className="h-3.5 w-3.5" />}
            >
              Vault ({documents.length})
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {/* ======================================================== */}
      {/* TAB 1: OVERVIEW */}
      {/* ======================================================== */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Biographical & Identity */}
          <Card>
            <CardHeader>
              <CardTitle>Biographical & Civil Identity</CardTitle>
              <CardDescription>
                Verified civil and personal demographic coordinates.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Full Legal Name</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {student.firstName} {student.lastName}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Gender</span>
                <span className="text-slate-800 dark:text-slate-200">
                  {student.gender}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Date of Birth</span>
                <span className="text-slate-800 dark:text-slate-200 font-mono">
                  {student.dateOfBirth}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Blood Group</span>
                <span className="font-mono font-semibold text-indigo-600 dark:text-indigo-400">
                  {student.bloodGroup}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Admission Date</span>
                <span className="text-slate-800 dark:text-slate-200 font-mono">
                  {student.admissionDate}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5">
                <span className="text-slate-400">Admission Quota</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  {student.quota} Quota
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Residence & Primary Guardian */}
          <Card>
            <CardHeader>
              <CardTitle>Address & Residence</CardTitle>
              <CardDescription>
                Permanent postal address and campus residency status.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Street Address</span>
                <span className="text-slate-800 dark:text-slate-200">
                  {student.address.street}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">City / State</span>
                <span className="text-slate-800 dark:text-slate-200">
                  {student.address.city}, {student.address.state}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Postal Pincode</span>
                <span className="font-mono text-slate-800 dark:text-slate-200">
                  {student.address.pincode}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Campus Residence</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  {student.hostel ? student.hostel.hostelName : "Day Scholar"}
                </span>
              </div>
              {student.hostel && (
                <div className="grid grid-cols-2 py-1.5">
                  <span className="text-slate-400">Room / Bed Allocation</span>
                  <span className="font-mono text-indigo-600 dark:text-indigo-400 font-semibold">
                    {student.hostel.roomNumber} ({student.hostel.bed}) &bull;{" "}
                    {student.hostel.block}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 2: ACADEMIC & MILESTONES */}
      {/* ======================================================== */}
      {activeTab === "academic" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Academic Performance</CardTitle>
                <CardDescription>Cumulative GPA & Credits</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="text-2xl font-bold font-mono text-indigo-600 dark:text-indigo-400">
                  {student.academicStats.cgpa.toFixed(2)} CGPA
                </div>
                <p className="text-xs text-slate-500">
                  Total Credits Earned:{" "}
                  <span className="font-mono font-semibold">
                    {student.academicStats.totalCreditsEarned}
                  </span>{" "}
                  / 160
                </p>
                <p className="text-xs text-slate-500">
                  Institutional Cohort Rank:{" "}
                  <span className="font-mono font-semibold">
                    #{student.academicStats.rank}
                  </span>
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Degree Curriculum</CardTitle>
                <CardDescription>Four-Year B.Tech Program</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-xs">
                <div className="font-semibold text-slate-900 dark:text-white">
                  {student.program.name}
                </div>
                <p className="text-slate-500">
                  Department: {student.program.department}
                </p>
                <p className="text-slate-500">
                  Current Standing: Semester {student.currentSemester} &bull;
                  Section {student.section}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Attendance Summary</CardTitle>
                <CardDescription>Biometric & Lecture Logs</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
                  {student.attendanceSummary.overallPercentage}%
                </div>
                <p className="text-xs text-slate-500">
                  Attended:{" "}
                  <span className="font-mono">
                    {student.attendanceSummary.attendedClasses}
                  </span>{" "}
                  / {student.attendanceSummary.totalClasses} classes
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Academic Milestones */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-6">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Academic Milestones & Achievements
                </h3>
                <p className="text-xs text-slate-500">
                  Official timeline of verified achievements, honors, and degree
                  progression steps.
                </p>
              </div>
              {canAddMilestones && (
                <Button
                  size="sm"
                  variant="outline"
                  leftIcon={<Plus className="h-3.5 w-3.5" />}
                  onClick={() => setMilestoneModalOpen(true)}
                >
                  Log Milestone
                </Button>
              )}
            </div>

            {milestones.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">
                No academic milestones logged yet.
              </p>
            ) : (
              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
                {milestones.map((mls) => (
                  <div key={mls.id} className="relative group">
                    <div className="absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-indigo-600 bg-white dark:bg-slate-900" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-slate-400">
                          {mls.date}
                        </span>
                        {mls.semester && (
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                            Sem {mls.semester}
                          </span>
                        )}
                        <Badge
                          variant={
                            mls.status === "COMPLETED" ? "success" : "secondary"
                          }
                        >
                          {mls.category}
                        </Badge>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white mt-1">
                        {mls.title}
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {mls.description}
                      </p>
                      {mls.awardedBy && (
                        <p className="text-[11px] text-indigo-600 dark:text-indigo-400 font-medium mt-1">
                          Conferred by: {mls.awardedBy}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 3: GUARDIANS */}
      {/* ======================================================== */}
      {activeTab === "guardians" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Family & Guardian Relationships
              </h3>
              <p className="text-xs text-slate-500">
                Parents, legal guardians, and designated emergency contact
                coordinates.
              </p>
            </div>
            <Button
              size="sm"
              variant="primary"
              leftIcon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => setGuardianModalOpen(true)}
            >
              Add Guardian
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {guardians.map((grd) => (
              <div
                key={grd.id}
                className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-xs relative"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-base font-bold text-slate-900 dark:text-white">
                        {grd.name}
                      </h4>
                      <Badge variant="secondary">
                        {grd.relationLabel || grd.relation}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {grd.occupation}
                    </p>
                  </div>

                  <div className="flex items-center gap-1">
                    {grd.isPrimary && <Badge variant="success">Primary</Badge>}
                    {grd.isEmergencyContact && (
                      <Badge variant="warning">Emergency</Badge>
                    )}
                  </div>
                </div>

                <div className="mt-4 space-y-2 text-xs text-slate-600 dark:text-slate-300 border-t border-slate-100 dark:border-slate-800 pt-3">
                  <div className="flex items-center gap-2">
                    <Phone className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span className="font-mono">{grd.phone}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Mail className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span>{grd.email}</span>
                  </div>
                  {grd.annualIncome && (
                    <div className="flex items-center gap-2 text-slate-400">
                      <span>Annual Income:</span>
                      <span className="font-mono font-medium text-slate-700 dark:text-slate-300">
                        {grd.annualIncome}
                      </span>
                    </div>
                  )}
                  {grd.address && (
                    <div className="flex items-start gap-2 text-slate-400 pt-1">
                      <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                      <span>
                        {grd.address.street}, {grd.address.city},{" "}
                        {grd.address.state} - {grd.address.pincode}
                      </span>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                  <Button
                    size="sm"
                    variant="ghost"
                    leftIcon={<Trash2 className="h-3.5 w-3.5 text-rose-500" />}
                    onClick={() => handleDeleteGuardian(grd.id)}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 4: DOCUMENTS VAULT */}
      {/* ======================================================== */}
      {activeTab === "documents" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Student Document Repository & Vault
              </h3>
              <p className="text-xs text-slate-500">
                Official certified certificates, identity proofs, and academic
                credentials.
              </p>
            </div>
            <Button
              size="sm"
              variant="primary"
              leftIcon={<Upload className="h-3.5 w-3.5" />}
              onClick={() => setUploadDocModalOpen(true)}
            >
              Upload Document
            </Button>
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-xs">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Document Title</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Uploaded Date</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Verification Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {documents.map((doc) => (
                  <tr
                    key={doc.id}
                    className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition"
                  >
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-indigo-500 shrink-0" />
                        <div>
                          <div>{doc.name}</div>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {doc.fileSize}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[11px] font-mono text-slate-700 dark:text-slate-300">
                        {doc.category}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-500">
                      {doc.uploadedAt}
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={
                          doc.status === "VERIFIED"
                            ? "success"
                            : doc.status === "UNDER_REVIEW"
                              ? "warning"
                              : "destructive"
                        }
                        dot
                      >
                        {doc.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setPreviewDoc(doc)}
                        >
                          Preview
                        </Button>
                        {canVerifyDocs && doc.status !== "VERIFIED" && (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleVerifyDocument(doc.id)}
                          >
                            Verify
                          </Button>
                        )}
                        {canVerifyDocs && doc.status === "UNDER_REVIEW" && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleRejectDocument(doc.id)}
                            className="text-rose-500 hover:text-rose-600"
                          >
                            Reject
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 5: LIFECYCLE TIMELINE */}
      {/* ======================================================== */}
      {activeTab === "timeline" && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs">
          <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
            Student Institutional Lifecycle
          </h3>
          <p className="text-xs text-slate-500 mb-6">
            Chronological audit trail of admissions, enrollments, registrations,
            and milestones.
          </p>

          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
            {(student.recentActivity || []).map((act) => (
              <div key={act.id} className="relative">
                <div className="absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-indigo-600 bg-white dark:bg-slate-900" />
                <div className="text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-400">
                      {act.timestamp}
                    </span>
                    <Badge variant="secondary">{act.domain}</Badge>
                    <span className="text-slate-400">&bull;</span>
                    <span className="text-slate-500 font-medium">
                      Logged by {act.actor}
                    </span>
                  </div>
                  <p className="text-slate-800 dark:text-slate-200 font-medium mt-1">
                    {act.action}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 6: CONNECTED ENGINES (Cross-module Preparation) */}
      {/* ======================================================== */}
      {activeTab === "connected-modules" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-sm">
                <span>Attendance Engine</span>
                <Badge variant="success">Operational</Badge>
              </CardTitle>
              <CardDescription>
                Live session presence synchronization.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Cumulative Attendance</span>
                <span className="font-mono font-bold text-emerald-600">
                  {student.attendanceSummary.overallPercentage}%
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Status</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {student.attendanceSummary.status}
                </span>
              </div>
              <Link href={`/app/attendance/students/${student.id}`}>
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full mt-2"
                  rightIcon={<ExternalLink className="h-3 w-3" />}
                >
                  Open Full Attendance Sheet
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-sm">
                <span>Finance & Fee Billing</span>
                <Badge variant="secondary">Linked</Badge>
              </CardTitle>
              <CardDescription>
                Term tuition and student ledger balance.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Total Billed Fees</span>
                <span className="font-mono font-bold">
                  ₹ {student.financeSummary.totalBilled.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Pending Dues</span>
                <span className="font-mono text-emerald-600 font-bold">
                  ₹ {student.financeSummary.pendingDue.toLocaleString()}
                </span>
              </div>
              <Link href="/app/finance/invoices">
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full mt-2"
                  rightIcon={<ExternalLink className="h-3 w-3" />}
                >
                  View Finance Ledgers
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-sm">
                <span>Examinations & Gradebook</span>
                <Badge variant="secondary">Linked</Badge>
              </CardTitle>
              <CardDescription>
                Continuous assessments and transcript.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Cumulative GPA</span>
                <span className="font-mono font-bold text-indigo-600">
                  {student.academicStats.cgpa.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Standing Backlogs</span>
                <span className="font-mono font-bold text-emerald-600">
                  {student.academicStats.backlogs} Backlogs
                </span>
              </div>
              <Link href="/app/examinations/results">
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full mt-2"
                  rightIcon={<ExternalLink className="h-3 w-3" />}
                >
                  Open Academic Transcript
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-sm">
                <span>Placement & Careers</span>
                <Badge variant="success">Eligible</Badge>
              </CardTitle>
              <CardDescription>
                Corporate drives and shortlisting profile.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Active Applications</span>
                <span className="font-mono font-bold">
                  {student.placementSummary.appliedDrives} Drives
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Offers Extended</span>
                <span className="font-mono font-bold text-emerald-600">
                  {student.placementSummary.offersReceived} Offers
                </span>
              </div>
              <Link href="/app/placement">
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full mt-2"
                  rightIcon={<ExternalLink className="h-3 w-3" />}
                >
                  View Placement Drives
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODALS */}
      {/* ======================================================== */}

      {/* Lifecycle Status Modal */}
      <Dialog
        open={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        title="Update Student Lifecycle Status"
      >
        <form onSubmit={handleUpdateStatus} className="space-y-4 pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Select Lifecycle Status
            </label>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value as StudentStatus)}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
            >
              <option value="ACTIVE">ACTIVE — Good Academic Standing</option>
              <option value="ON_LEAVE">
                ON_LEAVE — Sabbatical / Leave of Absence
              </option>
              <option value="SUSPENDED">SUSPENDED — Disciplinary Hold</option>
              <option value="GRADUATED">GRADUATED — Degree Conferred</option>
              <option value="WITHDRAWN">
                WITHDRAWN — Transferred / Discontinued
              </option>
            </select>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setStatusModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isUpdatingStatus}
            >
              Record Transition
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Add Guardian Modal */}
      <Dialog
        open={guardianModalOpen}
        onClose={() => setGuardianModalOpen(false)}
        title="Add Guardian / Family Contact"
      >
        <form onSubmit={handleAddGuardian} className="space-y-4 pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Guardian Full Name *
            </label>
            <Input
              required
              value={guardianForm.name}
              onChange={(e) =>
                setGuardianForm({ ...guardianForm, name: e.target.value })
              }
              placeholder="e.g. Meenakshi Patel"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Relationship Type
              </label>
              <select
                value={guardianForm.relation}
                onChange={(e) =>
                  setGuardianForm({
                    ...guardianForm,
                    relation: e.target.value as GuardianRelationType,
                  })
                }
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="FATHER">Father</option>
                <option value="MOTHER">Mother</option>
                <option value="GUARDIAN">Legal / Local Guardian</option>
                <option value="SIBLING">Sibling</option>
                <option value="EMERGENCY_CONTACT">Emergency Contact</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Occupation
              </label>
              <Input
                value={guardianForm.occupation}
                onChange={(e) =>
                  setGuardianForm({
                    ...guardianForm,
                    occupation: e.target.value,
                  })
                }
                placeholder="e.g. Software Architect"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Phone Number *
              </label>
              <Input
                required
                value={guardianForm.phone}
                onChange={(e) =>
                  setGuardianForm({ ...guardianForm, phone: e.target.value })
                }
                placeholder="+91 98450 00000"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Email Address
              </label>
              <Input
                type="email"
                value={guardianForm.email}
                onChange={(e) =>
                  setGuardianForm({ ...guardianForm, email: e.target.value })
                }
                placeholder="guardian@example.com"
              />
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs pt-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={guardianForm.isPrimary}
                onChange={(e) =>
                  setGuardianForm({
                    ...guardianForm,
                    isPrimary: e.target.checked,
                  })
                }
                className="rounded border-slate-300 text-indigo-600"
              />
              <span>Primary Guardian</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={guardianForm.isEmergencyContact}
                onChange={(e) =>
                  setGuardianForm({
                    ...guardianForm,
                    isEmergencyContact: e.target.checked,
                  })
                }
                className="rounded border-slate-300 text-indigo-600"
              />
              <span>Emergency Contact</span>
            </label>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setGuardianModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Link Relationship
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Upload Document Modal */}
      <Dialog
        open={uploadDocModalOpen}
        onClose={() => setUploadDocModalOpen(false)}
        title="Upload Student Credential to Vault"
      >
        <form onSubmit={handleUploadDocument} className="space-y-4 pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Document Name / Title *
            </label>
            <Input
              required
              value={docName}
              onChange={(e) => setDocName(e.target.value)}
              placeholder="e.g. Senior Secondary School Certificate"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Document Category
              </label>
              <select
                value={docCategory}
                onChange={(e) =>
                  setDocCategory(e.target.value as DocumentCategory)
                }
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="IDENTITY">IDENTITY (Aadhaar / Passport)</option>
                <option value="ACADEMIC">ACADEMIC (Board Transcripts)</option>
                <option value="ADMISSION">ADMISSION (Allotment Memo)</option>
                <option value="FINANCIAL">
                  FINANCIAL (Scholarship Orders)
                </option>
                <option value="MEDICAL">MEDICAL (Fitness Certificates)</option>
                <option value="CERTIFICATES">
                  CERTIFICATES (Honors / Badges)
                </option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                File Size
              </label>
              <Input
                value={docFileSize}
                onChange={(e) => setDocFileSize(e.target.value)}
                placeholder="e.g. 1.8 MB"
              />
            </div>
          </div>

          <div className="p-4 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl text-center space-y-1 bg-slate-50/50 dark:bg-slate-800/40">
            <Upload className="h-6 w-6 text-slate-400 mx-auto" />
            <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
              Drag file here, or click to browse
            </p>
            <p className="text-[11px] text-slate-400">
              PDF, PNG, JPG up to 10MB
            </p>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setUploadDocModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Upload to Vault
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Document Preview Modal */}
      {previewDoc && (
        <Dialog
          open={Boolean(previewDoc)}
          onClose={() => setPreviewDoc(null)}
          title={`Document Vault Preview: ${previewDoc.name}`}
        >
          <div className="space-y-4 pt-2">
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-6 bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center min-h-[220px] text-center">
              <FileText className="h-16 w-16 text-indigo-500 mb-3" />
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                {previewDoc.name}
              </h4>
              <p className="text-xs text-slate-500 mt-1">
                Category: {previewDoc.category} &bull; File Size:{" "}
                {previewDoc.fileSize}
              </p>
              <p className="text-xs font-mono text-slate-400 mt-0.5">
                Uploaded on {previewDoc.uploadedAt} by {previewDoc.uploadedBy}
              </p>
              <div className="mt-3">
                <Badge
                  variant={
                    previewDoc.status === "VERIFIED" ? "success" : "warning"
                  }
                  dot
                >
                  {previewDoc.status}
                </Badge>
              </div>
            </div>

            <div className="flex justify-between items-center pt-2">
              <Button
                size="sm"
                variant="outline"
                leftIcon={<Download className="h-3.5 w-3.5" />}
              >
                Download Copy
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setPreviewDoc(null)}
              >
                Close Preview
              </Button>
            </div>
          </div>
        </Dialog>
      )}

      {/* Add Milestone Modal */}
      <Dialog
        open={milestoneModalOpen}
        onClose={() => setMilestoneModalOpen(false)}
        title="Record Academic Milestone"
      >
        <form onSubmit={handleAddMilestone} className="space-y-4 pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Milestone Title *
            </label>
            <Input
              required
              value={milestoneTitle}
              onChange={(e) => setMilestoneTitle(e.target.value)}
              placeholder="e.g. Dean's Honor Roll Distinction"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Category
              </label>
              <select
                value={milestoneCategory}
                onChange={(e) =>
                  setMilestoneCategory(e.target.value as MilestoneCategory)
                }
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="ACHIEVEMENT">
                  ACHIEVEMENT (Awards & Honors)
                </option>
                <option value="SEMESTER_PROGRESSION">
                  SEMESTER_PROGRESSION (Year Clearance)
                </option>
                <option value="INTERNSHIP">
                  INTERNSHIP (Industrial Training)
                </option>
                <option value="PLACEMENT">
                  PLACEMENT (Corporate Selection)
                </option>
                <option value="GRADUATION">GRADUATION (Degree Finality)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Semester
              </label>
              <select
                value={milestoneSemester}
                onChange={(e) => setMilestoneSemester(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Description & Details *
            </label>
            <textarea
              required
              rows={3}
              value={milestoneDesc}
              onChange={(e) => setMilestoneDesc(e.target.value)}
              placeholder="Provide context regarding the award, score, or event..."
              className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setMilestoneModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Record Milestone
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
