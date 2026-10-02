"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  FileCheck2,
  Search,
  Filter,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  Briefcase,
  Building2,
  Award,
  ChevronRight,
  Eye,
  Plus,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import { Application, ApplicationStatus, InterviewStage, JobDrive, Position } from "@/types/placement";

export default function ApplicationsManagementPage() {
  const { showToast } = useToast();
  const [applications, setApplications] = useState<Application[]>([]);
  const [drives, setDrives] = useState<JobDrive[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [stageFilter, setStageFilter] = useState<string>("ALL");

  // Rejection modal
  const [rejectModalAppId, setRejectModalAppId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const [appsRes, drivesRes, posRes] = await Promise.all([
        placementService.getApplications(),
        placementService.getJobDrives(),
        placementService.getPositions(),
      ]);
      setApplications(appsRes.data);
      setDrives(drivesRes.data);
      setPositions(posRes.data);
    } catch {
      showToast({ title: "Error", message: "Failed to load candidate applications", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleShortlist = async (appId: string) => {
    try {
      await placementService.shortlistApplications([appId], "Placement Officer");
      showToast({ title: "Shortlisted", message: "Candidate advanced to technical rounds", type: "success" });
      loadData();
    } catch {
      showToast({ title: "Error", message: "Failed to shortlist application", type: "error" });
    }
  };

  const handleConfirmReject = async () => {
    if (!rejectModalAppId) return;
    try {
      await placementService.rejectApplication(rejectModalAppId, rejectReason || "Does not meet candidate criteria", "Placement Officer");
      showToast({ title: "Application Rejected", message: "Candidate status updated to REJECTED", type: "info" });
      setRejectModalAppId(null);
      setRejectReason("");
      loadData();
    } catch {
      showToast({ title: "Error", message: "Failed to reject application", type: "error" });
    }
  };

  const filteredApplications = useMemo(() => {
    return applications.filter((app) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          app.applicationCode.toLowerCase().includes(q) ||
          app.studentName.toLowerCase().includes(q) ||
          app.rollNumber.toLowerCase().includes(q) ||
          app.companyName.toLowerCase().includes(q) ||
          app.positionTitle.toLowerCase().includes(q);
        if (!matches) return false;
      }

      if (statusFilter !== "ALL" && app.status !== statusFilter) {
        return false;
      }

      if (stageFilter !== "ALL" && app.currentStage !== stageFilter) {
        return false;
      }

      return true;
    });
  }, [applications, searchQuery, statusFilter, stageFilter]);

  const columns: ColumnDef<Application>[] = [
    {
      id: "code",
      header: "Application Code",
      sortable: true,
      cell: (item) => (
        <Link
          href={`/app/placement/applications/${item.id}`}
          className="font-mono font-semibold text-slate-900 hover:text-indigo-600 dark:text-slate-100 dark:hover:text-indigo-400"
        >
          {item.applicationCode}
        </Link>
      ),
    },
    {
      id: "student",
      header: "Candidate",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <Link
            href={`/app/placement/students/${item.studentId}`}
            className="font-medium text-slate-900 hover:text-indigo-600 dark:text-slate-100 dark:hover:text-indigo-400"
          >
            {item.studentName}
          </Link>
          <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
            <span className="font-mono">{item.rollNumber}</span>
            <span>•</span>
            <span>CGPA {item.cgpa.toFixed(2)}</span>
          </div>
        </div>
      ),
    },
    {
      id: "role",
      header: "Position & Recruiter",
      cell: (item) => (
        <div className="text-xs">
          <span className="font-semibold text-slate-900 dark:text-white">{item.positionTitle}</span>
          <p className="text-slate-500 font-medium">{item.companyName}</p>
        </div>
      ),
    },
    {
      id: "appliedDate",
      header: "Applied Date",
      sortable: true,
      cell: (item) => (
        <span className="text-xs text-slate-600 dark:text-slate-300">
          {item.appliedDate.split("T")[0]}
        </span>
      ),
    },
    {
      id: "stage",
      header: "Current Stage",
      cell: (item) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
          {item.currentStage}
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (item) => {
        const badgeColors: Record<ApplicationStatus, "success" | "warning" | "destructive" | "secondary" | "info"> = {
          SELECTED: "success",
          SHORTLISTED: "info",
          SUBMITTED: "warning",
          UNDER_REVIEW: "warning",
          REJECTED: "destructive",
          WITHDRAWN: "secondary",
          DRAFT: "secondary",
        };
        return (
          <Badge variant={badgeColors[item.status] || "secondary"} dot>
            {item.status}
          </Badge>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      align: "right",
      cell: (item) => (
        <div className="flex items-center justify-end gap-1.5">
          {item.status === "SUBMITTED" && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleShortlist(item.id)}
                className="h-7 text-xs text-emerald-600 hover:text-emerald-700"
              >
                Shortlist
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setRejectModalAppId(item.id)}
                className="h-7 text-xs text-rose-600 hover:text-rose-700"
              >
                Reject
              </Button>
            </>
          )}
          <Link href={`/app/placement/applications/${item.id}`}>
            <Button variant="ghost" size="sm" className="h-7 text-xs">
              Review
            </Button>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-1">
            <Link href="/app/placement" className="hover:text-indigo-600 dark:hover:text-indigo-400">
              Placement Hub
            </Link>
            <span>/</span>
            <span>Applications</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Candidate Application Submissions & Shortlisting
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Review applicant qualifications, verify drive eligibility snapshots, manage candidate shortlists, and track recruitment progression.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Applications"
          value={applications.length}
          icon={<FileCheck2 className="w-5 h-5 text-indigo-500" />}
          description="Submissions across all drives"
        />
        <StatCard
          title="Candidates Shortlisted"
          value={applications.filter((a) => a.status === "SHORTLISTED").length}
          icon={<CheckCircle2 className="w-5 h-5 text-sky-500" />}
          description="Advanced to interview rounds"
        />
        <StatCard
          title="Pending Review"
          value={applications.filter((a) => a.status === "SUBMITTED").length}
          icon={<Clock className="w-5 h-5 text-amber-500" />}
          description="Awaiting placement team action"
        />
        <StatCard
          title="Final Selections"
          value={applications.filter((a) => a.status === "SELECTED").length}
          icon={<Award className="w-5 h-5 text-emerald-500" />}
          description="Offers extended to candidates"
        />
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search candidate, code, role, company..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Application Statuses</option>
            <option value="SUBMITTED">Submitted (Pending Review)</option>
            <option value="SHORTLISTED">Shortlisted</option>
            <option value="SELECTED">Selected</option>
            <option value="REJECTED">Rejected</option>
            <option value="WITHDRAWN">Withdrawn</option>
          </Select>

          <Select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Recruitment Stages</option>
            <option value="APPLICATION">Application Stage</option>
            <option value="TECHNICAL">Technical Round</option>
            <option value="HR">HR Round</option>
            <option value="OFFER">Offer Stage</option>
            <option value="OUTCOME">Placement Outcome</option>
          </Select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:bg-slate-900 dark:border-slate-800">
        <DataGrid
          data={filteredApplications}
          columns={columns}
          keyExtractor={(item) => item.id}
          loading={loading}
          paginated
          pageSize={10}
          emptyMessage="No candidate applications found matching the selected filters."
        />
      </div>

      {/* Reject Reason Modal */}
      {rejectModalAppId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Reject Application</h3>
            <p className="text-xs text-slate-400">
              Provide justification for candidate rejection. Recorded in audit log.
            </p>

            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Inadequate domain experience or coding round score below cutoff."
              rows={3}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white text-xs"
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" size="sm" onClick={() => setRejectModalAppId(null)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleConfirmReject} className="bg-rose-600 hover:bg-rose-700 text-white">
                Confirm Rejection
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
