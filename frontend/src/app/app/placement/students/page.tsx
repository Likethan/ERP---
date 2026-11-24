"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Users,
  Search,
  Filter,
  GraduationCap,
  Award,
  Briefcase,
  ChevronRight,
  FileCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
  Building2,
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
import { formatLPA } from "@/services/placement-calculator";
import {
  StudentPlacementProfile,
  PlacementStatus,
  ResumeStatus,
} from "@/types/placement";

export default function StudentPlacementDirectoryPage() {
  const { showToast } = useToast();
  const [profiles, setProfiles] = useState<StudentPlacementProfile[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [resumeFilter, setResumeFilter] = useState<string>("ALL");
  const [cgpaFilter, setCgpaFilter] = useState<string>("ALL");

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await placementService.getPlacementStudents();
      setProfiles(res.data);
    } catch {
      showToast({
        title: "Error",
        message: "Failed to load student placement profiles",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered dataset
  const filteredProfiles = useMemo(() => {
    return profiles.filter((p) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          p.studentName.toLowerCase().includes(q) ||
          p.rollNumber.toLowerCase().includes(q) ||
          p.department.toLowerCase().includes(q) ||
          (p.placedCompany && p.placedCompany.toLowerCase().includes(q)) ||
          p.skills.programmingLanguages.some((lang) =>
            lang.toLowerCase().includes(q),
          ) ||
          p.skills.technical.some((tech) => tech.toLowerCase().includes(q));
        if (!matches) return false;
      }

      if (departmentFilter !== "ALL" && p.department !== departmentFilter) {
        return false;
      }

      if (statusFilter !== "ALL" && p.placementStatus !== statusFilter) {
        return false;
      }

      if (resumeFilter !== "ALL" && p.resumeStatus !== resumeFilter) {
        return false;
      }

      if (cgpaFilter !== "ALL") {
        const minCgpa = parseFloat(cgpaFilter);
        if (p.cgpa < minCgpa) return false;
      }

      return true;
    });
  }, [
    profiles,
    searchQuery,
    departmentFilter,
    statusFilter,
    resumeFilter,
    cgpaFilter,
  ]);

  // Summary Metrics
  const totalEligible = profiles.length;
  const placedCount = profiles.filter(
    (p) => p.placementStatus === "PLACED",
  ).length;
  const inProcessCount = profiles.filter(
    (p) => p.placementStatus === "IN_PROCESS",
  ).length;
  const unplacedCount = profiles.filter(
    (p) => p.placementStatus === "NOT_PLACED",
  ).length;
  const placementRate =
    totalEligible > 0 ? Math.round((placedCount / totalEligible) * 100) : 0;

  // Unique departments for filter
  const departments = useMemo(() => {
    return Array.from(new Set(profiles.map((p) => p.department)));
  }, [profiles]);

  const columns: ColumnDef<StudentPlacementProfile>[] = [
    {
      id: "student",
      header: "Candidate",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <Link
            href={`/app/placement/students/${item.id}`}
            className="font-medium text-slate-900 hover:text-indigo-600 dark:text-slate-100 dark:hover:text-indigo-400 transition-colors"
          >
            {item.studentName}
          </Link>
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            <span className="font-mono">{item.rollNumber}</span>
            <span>•</span>
            <span>{item.department}</span>
          </div>
        </div>
      ),
    },
    {
      id: "academic",
      header: "CGPA / Backlogs",
      sortable: true,
      cell: (item) => (
        <div className="text-xs">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-900 dark:text-slate-100">
              {item.cgpa.toFixed(2)} CGPA
            </span>
          </div>
          <div className="text-slate-500 dark:text-slate-400 mt-0.5">
            {item.activeBacklogs === 0 ? (
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                Clear (0 Backlogs)
              </span>
            ) : (
              <span className="text-rose-600 dark:text-rose-400 font-medium">
                {item.activeBacklogs} Active Backlog(s)
              </span>
            )}
          </div>
        </div>
      ),
    },
    {
      id: "skills",
      header: "Core Skills & Tech",
      cell: (item) => (
        <div className="flex flex-wrap gap-1 max-w-xs">
          {item.skills.programmingLanguages.slice(0, 3).map((lang) => (
            <span
              key={lang}
              className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
            >
              {lang}
            </span>
          ))}
          {item.skills.technical.slice(0, 1).map((tech) => (
            <span
              key={tech}
              className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300"
            >
              {tech}
            </span>
          ))}
          {item.skills.programmingLanguages.length > 3 && (
            <span className="text-[10px] text-slate-400 self-center">
              +{item.skills.programmingLanguages.length - 3}
            </span>
          )}
        </div>
      ),
    },
    {
      id: "resume",
      header: "Resume",
      cell: (item) => {
        const resumeStyles: Record<
          ResumeStatus,
          { color: string; label: string }
        > = {
          NOT_UPLOADED: {
            color:
              "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
            label: "Missing",
          },
          UPLOADED: {
            color:
              "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300",
            label: "Uploaded",
          },
          UNDER_REVIEW: {
            color:
              "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300",
            label: "Under Review",
          },
          VERIFIED: {
            color:
              "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300",
            label: "Verified",
          },
          REJECTED: {
            color:
              "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300",
            label: "Rejected",
          },
        };
        const st = resumeStyles[item.resumeStatus] || resumeStyles.NOT_UPLOADED;
        return (
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${st.color}`}
          >
            {st.label}
          </span>
        );
      },
    },
    {
      id: "activity",
      header: "Activity Funnel",
      cell: (item) => (
        <div className="flex items-center gap-3 text-xs text-slate-600 dark:text-slate-400">
          <span title="Applications Submitted">
            <strong className="text-slate-900 dark:text-slate-100">
              {item.applicationsCount}
            </strong>{" "}
            Apps
          </span>
          <span>•</span>
          <span title="Interviews Attended">
            <strong className="text-slate-900 dark:text-slate-100">
              {item.interviewsCount}
            </strong>{" "}
            Intv
          </span>
          <span>•</span>
          <span title="Offers Received">
            <strong className="text-emerald-600 dark:text-emerald-400 font-bold">
              {item.offersCount}
            </strong>{" "}
            Offers
          </span>
        </div>
      ),
    },
    {
      id: "placementStatus",
      header: "Placement Status",
      sortable: true,
      cell: (item) => {
        if (item.placementStatus === "PLACED") {
          return (
            <div className="text-xs">
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                PLACED
              </span>
              <p className="text-[11px] font-medium text-slate-700 dark:text-slate-300 truncate max-w-[140px] mt-0.5">
                {item.placedCompany}
              </p>
              <p className="text-[10px] font-mono text-emerald-700 dark:text-emerald-300 font-bold">
                {formatLPA(item.placedPackageLpa || 0)}
              </p>
            </div>
          );
        }

        if (item.placementStatus === "IN_PROCESS") {
          return (
            <Badge variant="warning" dot>
              IN PROCESS
            </Badge>
          );
        }

        return (
          <Badge variant="secondary" dot>
            NOT PLACED
          </Badge>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      align: "right",
      cell: (item) => (
        <div className="flex items-center justify-end gap-2">
          <Link href={`/app/placement/students/${item.id}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Eye className="w-3.5 h-3.5" />
              Profile 360°
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
            <span>Student Profiles</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Student Placement Profiles & Talent Roster
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Enterprise registry of graduating candidates, technical skill tags,
            verified resumes, and live placement outcomes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/placement/drives">
            <Button variant="outline" className="gap-2 text-xs">
              <Briefcase className="w-4 h-4" />
              View Active Drives
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Graduating Roster"
          value={totalEligible}
          icon={<Users className="w-5 h-5 text-indigo-500" />}
          description="Class of 2026 registered cohort"
        />
        <StatCard
          title="Students Placed"
          value={placedCount}
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-500" />}
          description={`${placementRate}% cohort placement rate`}
        />
        <StatCard
          title="In Active Recruitment"
          value={inProcessCount}
          icon={<Clock className="w-5 h-5 text-amber-500" />}
          description="Shortlisted / in interview rounds"
        />
        <StatCard
          title="Unplaced / Needs Bridge"
          value={unplacedCount}
          icon={<AlertCircle className="w-5 h-5 text-rose-500" />}
          description="Candidates awaiting drive matches"
        />
      </div>

      {/* Filter Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:bg-slate-900 dark:border-slate-800 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search candidate, roll, skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>

          {/* Department Filter */}
          <Select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Departments</option>
            {departments.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </Select>

          {/* Placement Status */}
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Placement Statuses</option>
            <option value="PLACED">Placed</option>
            <option value="IN_PROCESS">In Process</option>
            <option value="NOT_PLACED">Not Placed</option>
          </Select>

          {/* Resume Status */}
          <Select
            value={resumeFilter}
            onChange={(e) => setResumeFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Resume States</option>
            <option value="VERIFIED">Verified Resumes</option>
            <option value="UNDER_REVIEW">Under Review</option>
            <option value="NOT_UPLOADED">Missing Resume</option>
          </Select>

          {/* CGPA Range */}
          <Select
            value={cgpaFilter}
            onChange={(e) => setCgpaFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All CGPA Ranges</option>
            <option value="8.5">CGPA ≥ 8.5 (Super Dream)</option>
            <option value="7.5">CGPA ≥ 7.5 (Dream)</option>
            <option value="6.5">CGPA ≥ 6.5 (Standard)</option>
          </Select>
        </div>
      </div>

      {/* Main DataGrid */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:bg-slate-900 dark:border-slate-800">
        <DataGrid
          data={filteredProfiles}
          columns={columns}
          keyExtractor={(item) => item.id}
          loading={loading}
          paginated
          pageSize={10}
          emptyMessage="No student placement profiles found matching the selected filters."
        />
      </div>
    </div>
  );
}
