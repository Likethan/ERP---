"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Briefcase,
  Search,
  Plus,
  Calendar,
  Clock,
  Building2,
  Users,
  Award,
  CheckCircle2,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  FileCheck2,
  AlertCircle,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import { JobDrive, DriveStatus, DriveType, Company } from "@/types/placement";

export default function JobDrivesDirectoryPage() {
  const { showToast } = useToast();
  const [drives, setDrives] = useState<JobDrive[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // 7-Step Guided Creation Workflow State
  const [showWizard, setShowWizard] = useState(false);
  const [wizardStep, setWizardStep] = useState(1);
  const [wizardData, setWizardData] = useState({
    companyId: "",
    title: "",
    driveType: "ON_CAMPUS" as DriveType,
    location: "Main Auditorium & Labs",
    applicationDeadline: new Date(Date.now() + 7 * 86400000)
      .toISOString()
      .split("T")[0],
    driveDate: new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0],
    batchGraduationYear: 2026,
    positionTitle: "Associate Software Engineer",
    departmentFunction: "Core Engineering",
    vacancies: 5,
    targetPrograms:
      "B.Tech Computer Science & Engineering, B.Tech Electronics & Communication",
    minCgpa: 7.5,
    maxBacklogs: 0,
    requiredSkills: "Java, Python, Data Structures, SQL",
    ctcLpa: 12.0,
    baseSalaryLpa: 10.0,
    stipendMonthly: 50000,
    description: "Annual university campus hiring drive.",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [drivesRes, companiesRes] = await Promise.all([
        placementService.getJobDrives(),
        placementService.getCompanies(),
      ]);
      setDrives(drivesRes.data);
      setCompanies(companiesRes.data);
      if (companiesRes.data.length > 0) {
        setWizardData((prev) => ({
          ...prev,
          companyId: companiesRes.data[0].id,
        }));
      }
    } catch {
      showToast({
        title: "Error",
        message: "Failed to load job drives",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveDraftDrive = async () => {
    const selectedComp = companies.find((c) => c.id === wizardData.companyId);
    try {
      const createdDrive = await placementService.createJobDrive({
        companyId: wizardData.companyId,
        companyName: selectedComp?.name,
        companyTier: selectedComp?.tier,
        title:
          wizardData.title || `${selectedComp?.name} Campus Recruitment 2026`,
        driveType: wizardData.driveType,
        location: wizardData.location,
        applicationDeadline: wizardData.applicationDeadline,
        driveDate: wizardData.driveDate,
        batchGraduationYear: wizardData.batchGraduationYear,
        description: wizardData.description,
      });

      // Also create the position
      await placementService.createPosition({
        driveId: createdDrive.data.id,
        driveCode: createdDrive.data.code,
        companyId: wizardData.companyId,
        companyName: selectedComp?.name,
        title: wizardData.positionTitle,
        departmentFunction: wizardData.departmentFunction,
        vacancies: wizardData.vacancies,
        ctcLpa: wizardData.ctcLpa,
        baseSalaryLpa: wizardData.baseSalaryLpa,
        stipendMonthly: wizardData.stipendMonthly,
        minCgpa: wizardData.minCgpa,
        maxBacklogs: wizardData.maxBacklogs,
        requiredSkills: wizardData.requiredSkills
          .split(",")
          .map((s) => s.trim()),
        targetPrograms: wizardData.targetPrograms
          .split(",")
          .map((p) => p.trim()),
      });

      showToast({
        title: "Drive Created",
        message:
          "Job drive registered as DRAFT (Senate/Officer approval required to open)",
        type: "success",
      });
      setShowWizard(false);
      setWizardStep(1);
      loadData();
    } catch {
      showToast({
        title: "Error",
        message: "Failed to create recruitment drive",
        type: "error",
      });
    }
  };

  const filteredDrives = useMemo(() => {
    return drives.filter((d) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          d.title.toLowerCase().includes(q) ||
          d.companyName.toLowerCase().includes(q) ||
          d.code.toLowerCase().includes(q) ||
          d.location.toLowerCase().includes(q);
        if (!matches) return false;
      }

      if (statusFilter !== "ALL" && d.status !== statusFilter) {
        return false;
      }

      return true;
    });
  }, [drives, searchQuery, statusFilter]);

  const columns: ColumnDef<JobDrive>[] = [
    {
      id: "drive",
      header: "Job Drive",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <Link
            href={`/app/placement/drives/${item.id}`}
            className="font-medium text-slate-900 hover:text-indigo-600 dark:text-slate-100 dark:hover:text-indigo-400 transition-colors"
          >
            {item.title}
          </Link>
          <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
            <span className="font-mono font-medium">{item.code}</span>
            <span>•</span>
            <span className="font-medium text-indigo-600 dark:text-indigo-400">
              {item.companyName}
            </span>
          </div>
        </div>
      ),
    },
    {
      id: "schedule",
      header: "Drive Date / Deadline",
      sortable: true,
      cell: (item) => (
        <div className="text-xs">
          <div className="flex items-center gap-1.5 font-medium text-slate-900 dark:text-white">
            <Calendar className="w-3.5 h-3.5 text-indigo-500" />
            <span>{item.driveDate}</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Deadline:{" "}
            <strong className="text-rose-600 dark:text-rose-400">
              {item.applicationDeadline}
            </strong>
          </p>
        </div>
      ),
    },
    {
      id: "positions",
      header: "Positions",
      cell: (item) => (
        <div className="text-xs">
          <span className="font-bold text-slate-900 dark:text-white">
            {item.positionsCount}
          </span>
          <span className="text-slate-500 ml-1">roles</span>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {item.driveType.replace(/_/g, " ")}
          </p>
        </div>
      ),
    },
    {
      id: "funnel",
      header: "Funnel Progress",
      cell: (item) => (
        <div className="text-xs text-slate-600 dark:text-slate-400 space-y-0.5">
          <div className="flex items-center gap-2">
            <span>
              <strong>{item.applicantsCount}</strong> Applied
            </span>
            <span>•</span>
            <span>
              <strong>{item.shortlistedCount}</strong> Shortlist
            </span>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <span>{item.interviewsCount} Intv</span>
            <span>•</span>
            <strong className="text-emerald-600 dark:text-emerald-400 font-bold">
              {item.offersCount} Offers
            </strong>
          </div>
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (item) => {
        const statusBadges: Record<
          DriveStatus,
          "success" | "warning" | "secondary" | "destructive"
        > = {
          OPEN: "success",
          UPCOMING: "warning",
          DRAFT: "secondary",
          CLOSED: "secondary",
          COMPLETED: "success",
          CANCELLED: "destructive",
        };
        return (
          <Badge variant={statusBadges[item.status] || "secondary"} dot>
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
          <Link href={`/app/placement/drives/${item.id}`}>
            <Button variant="outline" size="sm" className="h-7 text-xs gap-1">
              Drive 360°
              <ChevronRight className="w-3.5 h-3.5" />
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
            <Link
              href="/app/placement"
              className="hover:text-indigo-600 dark:hover:text-indigo-400"
            >
              Placement Hub
            </Link>
            <span>/</span>
            <span>Job Drives</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Campus Recruitment Drives & Hiring Events
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Manage corporate campus recruitment cycles, registration deadlines,
            position requirements, and candidate conversion pipelines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            onClick={() => setShowWizard(true)}
            className="gap-2 text-xs"
          >
            <Plus className="w-4 h-4" />
            Create Job Drive
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Drives"
          value={drives.filter((d) => d.status === "OPEN").length}
          icon={<Briefcase className="w-5 h-5 text-emerald-500" />}
          description="Open for candidate applications"
        />
        <StatCard
          title="Upcoming Drives"
          value={drives.filter((d) => d.status === "UPCOMING").length}
          icon={<Clock className="w-5 h-5 text-amber-500" />}
          description="Scheduled for future weeks"
        />
        <StatCard
          title="Total Applications"
          value={drives.reduce((sum, d) => sum + d.applicantsCount, 0)}
          icon={<Users className="w-5 h-5 text-indigo-500" />}
          description="Across all recruitment cycles"
        />
        <StatCard
          title="Total Offers Extended"
          value={drives.reduce((sum, d) => sum + d.offersCount, 0)}
          icon={<Award className="w-5 h-5 text-teal-500" />}
          description="Successful campus appointments"
        />
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search drive name, company, code, venue..."
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
            <option value="ALL">All Drive Statuses</option>
            <option value="OPEN">Open (Accepting Applications)</option>
            <option value="UPCOMING">Upcoming</option>
            <option value="DRAFT">Draft</option>
            <option value="CLOSED">Applications Closed</option>
            <option value="COMPLETED">Completed</option>
          </Select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:bg-slate-900 dark:border-slate-800">
        <DataGrid
          data={filteredDrives}
          columns={columns}
          keyExtractor={(item) => item.id}
          loading={loading}
          paginated
          pageSize={10}
          emptyMessage="No campus job drives found matching the selected criteria."
        />
      </div>

      {/* 7-Step Guided Creation Workflow Modal */}
      {showWizard && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            {/* Wizard Step Indicator */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white">
                  Create Recruitment Drive Workflow
                </h3>
                <p className="text-xs text-slate-400">
                  Step {wizardStep} of 7: Guided Drive Creation
                </p>
              </div>
              <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/50 px-2 py-1 rounded">
                DRAFT STAGE
              </span>
            </div>

            {/* Step 1: Company */}
            {wizardStep === 1 && (
              <div className="space-y-4 text-xs">
                <h4 className="font-semibold text-slate-200 text-sm">
                  Step 1 — Select Corporate Recruiter
                </h4>
                <p className="text-slate-400">
                  Choose the empanelled corporate partner for this drive.
                </p>
                <div>
                  <label className="text-slate-300 font-medium">
                    Corporate Partner *
                  </label>
                  <select
                    value={wizardData.companyId}
                    onChange={(e) =>
                      setWizardData({
                        ...wizardData,
                        companyId: e.target.value,
                      })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-white text-xs"
                  >
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.tier.replace(/_/g, " ")}) — {c.industry}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Step 2: Drive Details */}
            {wizardStep === 2 && (
              <div className="space-y-4 text-xs">
                <h4 className="font-semibold text-slate-200 text-sm">
                  Step 2 — Drive Title & Schedule
                </h4>
                <div className="space-y-3">
                  <div>
                    <label className="text-slate-300 font-medium">
                      Drive Title *
                    </label>
                    <Input
                      value={wizardData.title}
                      onChange={(e) =>
                        setWizardData({ ...wizardData, title: e.target.value })
                      }
                      placeholder="e.g. Google Cloud Graduate Engineering Drive 2026"
                      className="mt-1"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-slate-300 font-medium">
                        Drive Mode
                      </label>
                      <select
                        value={wizardData.driveType}
                        onChange={(e) =>
                          setWizardData({
                            ...wizardData,
                            driveType: e.target.value as DriveType,
                          })
                        }
                        className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white text-xs"
                      >
                        <option value="ON_CAMPUS">On Campus</option>
                        <option value="VIRTUAL">Virtual</option>
                        <option value="OFF_CAMPUS">Off Campus</option>
                        <option value="POOLED">Pooled Drive</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-slate-300 font-medium">
                        Venue / Platform
                      </label>
                      <Input
                        value={wizardData.location}
                        onChange={(e) =>
                          setWizardData({
                            ...wizardData,
                            location: e.target.value,
                          })
                        }
                        className="mt-1"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-slate-300 font-medium">
                        Application Deadline *
                      </label>
                      <Input
                        type="date"
                        value={wizardData.applicationDeadline}
                        onChange={(e) =>
                          setWizardData({
                            ...wizardData,
                            applicationDeadline: e.target.value,
                          })
                        }
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-slate-300 font-medium">
                        Drive Date *
                      </label>
                      <Input
                        type="date"
                        value={wizardData.driveDate}
                        onChange={(e) =>
                          setWizardData({
                            ...wizardData,
                            driveDate: e.target.value,
                          })
                        }
                        className="mt-1"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Positions */}
            {wizardStep === 3 && (
              <div className="space-y-4 text-xs">
                <h4 className="font-semibold text-slate-200 text-sm">
                  Step 3 — Job Positions Offered
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300 font-medium">
                      Position Title *
                    </label>
                    <Input
                      value={wizardData.positionTitle}
                      onChange={(e) =>
                        setWizardData({
                          ...wizardData,
                          positionTitle: e.target.value,
                        })
                      }
                      placeholder="e.g. Software Engineer"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-slate-300 font-medium">
                      Function / Practice
                    </label>
                    <Input
                      value={wizardData.departmentFunction}
                      onChange={(e) =>
                        setWizardData({
                          ...wizardData,
                          departmentFunction: e.target.value,
                        })
                      }
                      className="mt-1"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Estimated Open Vacancies
                  </label>
                  <Input
                    type="number"
                    value={wizardData.vacancies}
                    onChange={(e) =>
                      setWizardData({
                        ...wizardData,
                        vacancies: parseInt(e.target.value) || 1,
                      })
                    }
                    className="mt-1"
                  />
                </div>
              </div>
            )}

            {/* Step 4: Eligibility Cutoffs */}
            {wizardStep === 4 && (
              <div className="space-y-4 text-xs">
                <h4 className="font-semibold text-slate-200 text-sm">
                  Step 4 — Academic Eligibility Cutoffs
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300 font-medium">
                      Minimum CGPA Cutoff
                    </label>
                    <Input
                      type="number"
                      step="0.1"
                      value={wizardData.minCgpa}
                      onChange={(e) =>
                        setWizardData({
                          ...wizardData,
                          minCgpa: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="mt-1 font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-300 font-medium">
                      Max Active Backlogs Allowed
                    </label>
                    <Input
                      type="number"
                      value={wizardData.maxBacklogs}
                      onChange={(e) =>
                        setWizardData({
                          ...wizardData,
                          maxBacklogs: parseInt(e.target.value) || 0,
                        })
                      }
                      className="mt-1 font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-slate-300 font-medium">
                    Eligible Academic Programs
                  </label>
                  <Input
                    value={wizardData.targetPrograms}
                    onChange={(e) =>
                      setWizardData({
                        ...wizardData,
                        targetPrograms: e.target.value,
                      })
                    }
                    className="mt-1"
                  />
                </div>

                <div>
                  <label className="text-slate-300 font-medium">
                    Mandatory Skill Competencies
                  </label>
                  <Input
                    value={wizardData.requiredSkills}
                    onChange={(e) =>
                      setWizardData({
                        ...wizardData,
                        requiredSkills: e.target.value,
                      })
                    }
                    className="mt-1"
                  />
                </div>
              </div>
            )}

            {/* Step 5: Compensation */}
            {wizardStep === 5 && (
              <div className="space-y-4 text-xs">
                <h4 className="font-semibold text-slate-200 text-sm">
                  Step 5 — Compensation Package
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300 font-medium">
                      Total CTC (LPA) *
                    </label>
                    <Input
                      type="number"
                      step="0.5"
                      value={wizardData.ctcLpa}
                      onChange={(e) =>
                        setWizardData({
                          ...wizardData,
                          ctcLpa: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="mt-1 font-mono font-bold"
                    />
                  </div>
                  <div>
                    <label className="text-slate-300 font-medium">
                      Base Salary (LPA)
                    </label>
                    <Input
                      type="number"
                      step="0.5"
                      value={wizardData.baseSalaryLpa}
                      onChange={(e) =>
                        setWizardData({
                          ...wizardData,
                          baseSalaryLpa: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="mt-1 font-mono"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Monthly Internship Stipend (₹)
                  </label>
                  <Input
                    type="number"
                    value={wizardData.stipendMonthly}
                    onChange={(e) =>
                      setWizardData({
                        ...wizardData,
                        stipendMonthly: parseInt(e.target.value) || 0,
                      })
                    }
                    className="mt-1 font-mono"
                  />
                </div>
              </div>
            )}

            {/* Step 6: Review */}
            {wizardStep === 6 && (
              <div className="space-y-4 text-xs">
                <h4 className="font-semibold text-slate-200 text-sm">
                  Step 6 — Review Drive Specification
                </h4>
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Recruiter:</span>
                    <strong className="text-white">
                      {
                        companies.find((c) => c.id === wizardData.companyId)
                          ?.name
                      }
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Drive Title:</span>
                    <strong className="text-white">
                      {wizardData.title || "Standard Drive"}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Mode & Venue:</span>
                    <strong className="text-white">
                      {wizardData.driveType} ({wizardData.location})
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Drive Date:</span>
                    <strong className="text-white">
                      {wizardData.driveDate}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">
                      Application Deadline:
                    </span>
                    <strong className="text-rose-400 font-bold">
                      {wizardData.applicationDeadline}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Position & Package:</span>
                    <strong className="text-emerald-400 font-bold">
                      {wizardData.positionTitle} @ ₹{wizardData.ctcLpa} LPA
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Cutoff:</span>
                    <strong className="text-white">
                      Min CGPA {wizardData.minCgpa}, Max Backlogs{" "}
                      {wizardData.maxBacklogs}
                    </strong>
                  </div>
                </div>
              </div>
            )}

            {/* Step 7: Confirmation & Save DRAFT */}
            {wizardStep === 7 && (
              <div className="space-y-4 text-xs">
                <h4 className="font-semibold text-slate-200 text-sm">
                  Step 7 — Save as Draft
                </h4>
                <div className="p-4 rounded-xl border border-indigo-900/60 bg-indigo-950/30 text-indigo-300 space-y-2">
                  <AlertCircle className="w-5 h-5 text-indigo-400" />
                  <p className="font-medium">
                    As per institutional placement governance, new recruitment
                    drives are saved as <strong>DRAFT</strong>.
                  </p>
                  <p className="text-slate-400">
                    The placement director or coordinator can review positions
                    and publish to student portals when ready.
                  </p>
                </div>
              </div>
            )}

            {/* Wizard Navigation Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                disabled={wizardStep === 1}
                onClick={() => setWizardStep((prev) => Math.max(1, prev - 1))}
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Previous
              </Button>

              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowWizard(false)}
                >
                  Cancel
                </Button>

                {wizardStep < 7 ? (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() =>
                      setWizardStep((prev) => Math.min(7, prev + 1))
                    }
                  >
                    Next
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleSaveDraftDrive}
                  >
                    Save as DRAFT
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
