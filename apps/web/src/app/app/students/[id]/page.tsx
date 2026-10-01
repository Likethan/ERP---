"use client";

import React, { use, useEffect, useState } from "react";
import Link from "next/link";
import { studentsService } from "@/services/students.service";
import { StudentComprehensiveDetail } from "@/types/domain";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { Dialog } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast";
import {
  GraduationCap,
  Calendar,
  CheckCircle2,
  DollarSign,
  Briefcase,
  FileText,
  Clock,
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Shield,
  BedDouble,
  Bus,
  Edit,
  Download,
  AlertTriangle,
  History,
} from "lucide-react";

export default function StudentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const studentId = resolvedParams.id;
  const { showToast } = useToast();

  const [student, setStudent] = useState<StudentComprehensiveDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // Status edit modal
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [newStatus, setNewStatus] = useState<StudentComprehensiveDetail["status"]>("ACTIVE");
  const [statusReason, setStatusReason] = useState("");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  const loadStudent = async () => {
    setLoading(true);
    const res = await studentsService.getById(studentId);
    if (res.data) {
      setStudent(res.data);
      setNewStatus(res.data.status);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadStudent();
  }, [studentId]);

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!student) return;
    setIsUpdatingStatus(true);
    try {
      await studentsService.update(student.id, {
        status: newStatus,
      });
      showToast({
        type: "success",
        title: "Lifecycle Status Updated",
        message: `Student status transition recorded to ${newStatus}.`,
      });
      setStatusModalOpen(false);
      loadStudent();
    } catch {
      showToast({
        type: "error",
        title: "Update Failed",
        message: "Unable to update student status.",
      });
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center text-slate-400">
        Resolving Canonical Student Master Record...
      </div>
    );
  }

  if (!student) {
    return (
      <div className="space-y-4">
        <Link href="/app/students">
          <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Directory
          </Button>
        </Link>
        <EmptyState
          title="Student Record Not Found"
          description={`No student master profile exists with identifier "${studentId}".`}
          actionLabel="Return to Students"
          onAction={() => window.location.href = "/app/students"}
        />
      </div>
    );
  }

  const TABS = [
    { id: "overview", label: "Overview & Bio" },
    { id: "academics", label: "Academics & Schedule" },
    { id: "attendance", label: "Attendance Summary" },
    { id: "finance", label: "Finance & Fees" },
    { id: "placement", label: "Career & Placement" },
    { id: "documents", label: "Documents Vault" },
    { id: "activity", label: "Activity Timeline" },
  ];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link href="/app/students">
          <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Directory
          </Button>
        </Link>
      </div>

      {/* Main Student Header Banner */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 text-2xl font-bold font-mono shrink-0">
              {student.firstName[0]}
              {student.lastName[0]}
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  {student.firstName} {student.lastName}
                </h1>
                <Badge variant={student.status === "ACTIVE" ? "success" : "warning"} dot>
                  {student.status}
                </Badge>
                <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-300 border border-slate-700">
                  {student.rollNumber}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-400">
                {student.program.name} • {student.academicYear} • Semester {student.currentSemester} (Sec {student.section})
              </p>
              <div className="mt-2.5 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-slate-500" />
                  {student.email}
                </span>
                <span className="flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5 text-slate-500" />
                  {student.phone}
                </span>
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5 text-slate-500" />
                  {student.address.city}, {student.address.state}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              onClick={() => setStatusModalOpen(true)}
              variant="outline"
              size="sm"
              leftIcon={<Edit className="h-3.5 w-3.5" />}
            >
              Update Status
            </Button>
            <Link href="/app/documents">
              <Button variant="primary" size="sm" leftIcon={<FileText className="h-3.5 w-3.5" />}>
                Certificates
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {/* TAB CONTENT: Overview */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Biographical Information */}
          <Card>
            <CardHeader>
              <CardTitle>Biographical & Identity Information</CardTitle>
              <CardDescription>Verified civil and personal attributes.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Registration Number</span>
                <span className="font-mono text-slate-200">{student.registrationNumber}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Gender</span>
                <span className="text-slate-200">{student.gender}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Date of Birth</span>
                <span className="text-slate-200">{student.dateOfBirth}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Blood Group</span>
                <span className="font-mono text-slate-200">{student.bloodGroup}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Admission Date</span>
                <span className="text-slate-200">{student.admissionDate}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5">
                <span className="text-slate-400">Admission Quota</span>
                <span className="font-semibold text-indigo-400">{student.quota}</span>
              </div>
            </CardContent>
          </Card>

          {/* Guardian & Emergency Contacts */}
          <Card>
            <CardHeader>
              <CardTitle>Parent / Guardian & Address</CardTitle>
              <CardDescription>Official family contacts and residence coordinates.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Guardian Name</span>
                <span className="font-semibold text-slate-200">{student.guardian.name}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Relationship</span>
                <span className="text-slate-200">{student.guardian.relation}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Guardian Phone</span>
                <span className="font-mono text-slate-200">{student.guardian.phone}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Occupation</span>
                <span className="text-slate-200">{student.guardian.occupation}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5">
                <span className="text-slate-400">Permanent Address</span>
                <span className="text-slate-200 leading-relaxed">
                  {student.address.street}, {student.address.city}, {student.address.state} - {student.address.pincode}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Campus Infrastructure Logistics */}
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Campus Residential & Transport Logistics</CardTitle>
              <CardDescription>Institutional amenities linked to this student record.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              {student.hostel ? (
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1.5">
                  <div className="flex items-center gap-2 font-semibold text-white">
                    <BedDouble className="h-4 w-4 text-indigo-400" />
                    Hostel Accommodation
                  </div>
                  <div className="text-slate-300">{student.hostel.hostelName}</div>
                  <div className="text-slate-400 text-[11px]">
                    {student.hostel.block} • Room {student.hostel.roomNumber} ({student.hostel.bed})
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-xl border border-dashed border-slate-800 text-slate-500">
                  Day Scholar (No hostel allocation)
                </div>
              )}

              {student.transport ? (
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1.5">
                  <div className="flex items-center gap-2 font-semibold text-white">
                    <Bus className="h-4 w-4 text-emerald-400" />
                    Transport Subscription
                  </div>
                  <div className="text-slate-300">
                    {student.transport.routeCode} — {student.transport.routeName}
                  </div>
                  <div className="text-slate-400 text-[11px]">
                    Stop: {student.transport.stopName} • Bus {student.transport.busNumber}
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-xl border border-dashed border-slate-800 text-slate-500">
                  No institutional bus subscription
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB CONTENT: Academics */}
      {activeTab === "academics" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="p-4">
              <div className="text-xs text-slate-400">Cumulative GPA (CGPA)</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {student.academicStats.cgpa.toFixed(2)}
              </div>
              <div className="text-[11px] text-emerald-400 mt-0.5">Rank #{student.academicStats.rank} in Dept</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-slate-400">Credits Earned</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {student.academicStats.totalCreditsEarned} / 160
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">60% Degree Completion</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-slate-400">Active Backlogs</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {student.academicStats.backlogs}
              </div>
              <div className="text-[11px] text-emerald-400 mt-0.5">Clear Examination Status</div>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Current Semester Registered Courses (Sem {student.currentSemester})</CardTitle>
              <CardDescription>Continuous evaluation marks and lecture faculty assignments.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Course</TableHead>
                    <TableHead>Faculty</TableHead>
                    <TableHead>Credits</TableHead>
                    <TableHead>Attendance</TableHead>
                    <TableHead>Internal Marks</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {student.enrolledCourses.map((c) => (
                    <TableRow key={c.id}>
                      <TableCell>
                        <div className="font-semibold text-white">{c.code}</div>
                        <div className="text-slate-400 text-[11px]">{c.title}</div>
                      </TableCell>
                      <TableCell className="text-slate-300">{c.faculty}</TableCell>
                      <TableCell className="font-mono">{c.credits}</TableCell>
                      <TableCell>
                        <span className="font-mono font-semibold text-emerald-400">
                          {c.attendanceRate}%
                        </span>
                      </TableCell>
                      <TableCell className="font-mono font-medium text-slate-100">
                        {c.internalMarks} / 50
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB CONTENT: Attendance */}
      {activeTab === "attendance" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="p-4">
              <div className="text-xs text-slate-400">Overall Attendance</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {student.attendanceSummary.overallPercentage}%
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                {student.attendanceSummary.attendedClasses} of {student.attendanceSummary.totalClasses} classes
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-slate-400">Compliance Status</div>
              <div className="text-lg font-bold text-white mt-1">
                {student.attendanceSummary.status}
              </div>
              <div className="text-[11px] text-emerald-400 mt-0.5">Eligible for End-Sem Exam</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-slate-400">Leave Applications</div>
              <div className="text-lg font-bold text-white mt-1">
                1 Approved
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">On-Duty hackathon pass</div>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Attendance by Subject Breakdown</CardTitle>
              <CardDescription>Mandatory 75% attendance threshold per subject.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {student.enrolledCourses.map((c) => (
                <div key={c.id} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">{c.code} — {c.title}</span>
                    <span className="font-mono font-bold text-slate-200">{c.attendanceRate}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full"
                      style={{ width: `${c.attendanceRate}%` }}
                    />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB CONTENT: Finance */}
      {activeTab === "finance" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="p-4">
              <div className="text-xs text-slate-400">Total Billed Fees</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                ₹{student.financeSummary.totalBilled.toLocaleString()}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Academic Year 2026-27</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-slate-400">Total Paid Amount</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                ₹{student.financeSummary.totalPaid.toLocaleString()}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Cleared via UPI & Net Banking</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-slate-400">Current Outstanding Due</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                ₹{student.financeSummary.pendingDue.toLocaleString()}
              </div>
              <div className="text-[11px] text-emerald-400 mt-0.5">Account Status: CLEAR</div>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Invoices & Payment History</CardTitle>
                <CardDescription>Verified bursar receipts and installment records.</CardDescription>
              </div>
              <Link href="/app/finance/receipts">
                <Button variant="ghost" size="sm" className="text-xs text-slate-400 hover:text-white">
                  Receipts Archive
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-white">Annual Tuition & Laboratory Fee 2026-27</div>
                  <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                    Invoice: INV-2026-0891 • Paid on 14 Aug 2026
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-emerald-400">₹1,45,000</div>
                  <Badge variant="success" dot className="mt-0.5">PAID</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB CONTENT: Placement */}
      {activeTab === "placement" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="text-xs text-slate-400">Eligibility Status</div>
              <div className="text-lg font-bold text-emerald-400 mt-1">ELIGIBLE</div>
              <div className="text-[11px] text-slate-400 mt-0.5">CGPA ≥ 8.0 & 0 Backlogs</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-slate-400">Applied Drives</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {student.placementSummary.appliedDrives}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Recruitment applications</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-slate-400">Interviews Scheduled</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {student.placementSummary.interviewsScheduled}
              </div>
              <div className="text-[11px] text-indigo-400 mt-0.5">Round 2 active</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-slate-400">Official Offers</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {student.placementSummary.offersReceived}
              </div>
              <div className="text-[11px] text-emerald-400 mt-0.5">₹18.5 LPA (Cisco)</div>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recruitment Applications & Status</CardTitle>
              <CardDescription>Corporate drives applied for in 2026-27 campus cycle.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/40 flex items-center justify-between">
                <div>
                  <div className="font-bold text-white text-sm">Cisco Systems India</div>
                  <div className="text-slate-300">Software Development Engineer (Core Network OS)</div>
                  <div className="text-[11px] text-slate-400 mt-0.5 font-mono">Drive ID: drive-cisco-2026</div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-emerald-400 text-sm">₹18.5 LPA</div>
                  <Badge variant="success" dot className="mt-0.5">Shortlisted for Round 2</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB CONTENT: Documents */}
      {activeTab === "documents" && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Student Document Vault</CardTitle>
              <CardDescription>Digitally verified certificates, transcripts, and ID records.</CardDescription>
            </div>
            <Link href="/app/documents">
              <Button variant="outline" size="sm" leftIcon={<FileText className="h-3.5 w-3.5" />}>
                Request Certificate
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {student.documents.length > 0 ? (
              student.documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-800 bg-slate-950/40 text-xs"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-indigo-400 shrink-0" />
                    <div>
                      <div className="font-semibold text-white">{doc.name}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {doc.category} • {doc.fileSize} • Uploaded {doc.uploadDate}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.verified && <Badge variant="success">Verified</Badge>}
                    <Button variant="ghost" size="sm" leftIcon={<Download className="h-3.5 w-3.5" />}>
                      Download
                    </Button>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-500 text-xs">
                No external documents uploaded yet.
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB CONTENT: Activity */}
      {activeTab === "activity" && (
        <Card>
          <CardHeader>
            <CardTitle>Audit & Activity Timeline</CardTitle>
            <CardDescription>Verified provenance log of student events across CampusOS.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {student.recentActivity.map((act) => (
              <div key={act.id} className="flex items-start gap-3 text-xs">
                <div className="h-2 w-2 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                <div className="flex-1">
                  <div className="font-medium text-white">{act.action}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {act.timestamp} • Logged by {act.actor} ({act.domain})
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Update Status Modal */}
      <Dialog
        open={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        title="Update Student Lifecycle Status"
        description={`Modify enrollment lifecycle status for ${student.firstName} ${student.lastName}.`}
        maxWidth="md"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setStatusModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              isLoading={isUpdatingStatus}
              onClick={handleUpdateStatus}
            >
              Save Lifecycle Transition
            </Button>
          </>
        }
      >
        <form onSubmit={handleUpdateStatus} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              New Lifecycle Status
            </label>
            <Select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value as StudentComprehensiveDetail["status"])}
            >
              <option value="ACTIVE">ACTIVE — Full Academic Standing</option>
              <option value="ON_LEAVE">ON_LEAVE — Sabbatical / Medical Leave</option>
              <option value="SUSPENDED">SUSPENDED — Disciplinary Hold</option>
              <option value="WITHDRAWN">WITHDRAWN — Formal Program Exit</option>
              <option value="GRADUATED">GRADUATED — Degree Conferred</option>
            </Select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Justification & Administrative Memo
            </label>
            <Textarea
              rows={3}
              placeholder="Provide reason for status modification..."
              value={statusReason}
              onChange={(e) => setStatusReason(e.target.value)}
            />
          </div>
        </form>
      </Dialog>
    </div>
  );
}
