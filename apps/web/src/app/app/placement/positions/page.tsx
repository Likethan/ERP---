"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Layers,
  Search,
  Plus,
  Briefcase,
  Building2,
  MapPin,
  GraduationCap,
  Award,
  Users,
  CheckCircle2,
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
import { Position, EmploymentType, PositionStatus, JobDrive } from "@/types/placement";

export default function PositionsCatalogPage() {
  const { showToast } = useToast();
  const [positions, setPositions] = useState<Position[]>([]);
  const [drives, setDrives] = useState<JobDrive[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Create Modal
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    driveId: "",
    title: "",
    departmentFunction: "Software Engineering",
    employmentType: "FULL_TIME" as EmploymentType,
    location: "Bengaluru, Karnataka",
    vacancies: 5,
    ctcLpa: 12.0,
    baseSalaryLpa: 10.0,
    requiredSkills: "Java, Python, SQL, Docker",
    minCgpa: 7.5,
    maxBacklogs: 0,
    targetPrograms: "B.Tech Computer Science & Engineering, B.Tech Electronics & Communication",
    description: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [posRes, drivesRes] = await Promise.all([
        placementService.getPositions(),
        placementService.getJobDrives(),
      ]);
      setPositions(posRes.data);
      setDrives(drivesRes.data);
      if (drivesRes.data.length > 0) {
        setFormData((prev) => ({ ...prev, driveId: drivesRes.data[0].id }));
      }
    } catch {
      showToast({ title: "Error", message: "Failed to load positions catalog", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreatePosition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      showToast({ title: "Validation Error", message: "Position title is required", type: "error" });
      return;
    }

    try {
      await placementService.createPosition({
        driveId: formData.driveId,
        title: formData.title,
        departmentFunction: formData.departmentFunction,
        employmentType: formData.employmentType,
        location: formData.location,
        vacancies: Number(formData.vacancies),
        ctcLpa: Number(formData.ctcLpa),
        baseSalaryLpa: Number(formData.baseSalaryLpa),
        requiredSkills: formData.requiredSkills.split(",").map((s) => s.trim()).filter(Boolean),
        minCgpa: Number(formData.minCgpa),
        maxBacklogs: Number(formData.maxBacklogs),
        targetPrograms: formData.targetPrograms.split(",").map((p) => p.trim()).filter(Boolean),
        description: formData.description,
      });

      showToast({ title: "Success", message: `Position "${formData.title}" created`, type: "success" });
      setShowModal(false);
      loadData();
    } catch {
      showToast({ title: "Error", message: "Failed to create position", type: "error" });
    }
  };

  const filteredPositions = useMemo(() => {
    return positions.filter((p) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          p.title.toLowerCase().includes(q) ||
          p.companyName.toLowerCase().includes(q) ||
          p.departmentFunction.toLowerCase().includes(q) ||
          p.requiredSkills.some((s) => s.toLowerCase().includes(q));
        if (!matches) return false;
      }

      if (typeFilter !== "ALL" && p.employmentType !== typeFilter) {
        return false;
      }

      if (statusFilter !== "ALL" && p.status !== statusFilter) {
        return false;
      }

      return true;
    });
  }, [positions, searchQuery, typeFilter, statusFilter]);

  const columns: ColumnDef<Position>[] = [
    {
      id: "title",
      header: "Position Title",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <span className="font-semibold text-slate-900 dark:text-white">{item.title}</span>
          <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
            <span className="font-medium text-indigo-600 dark:text-indigo-400">{item.companyName}</span>
            <span>•</span>
            <span>{item.departmentFunction}</span>
          </div>
        </div>
      ),
    },
    {
      id: "type",
      header: "Type & Location",
      cell: (item) => (
        <div className="text-xs">
          <Badge variant="outline">{item.employmentType.replace("_", " ")}</Badge>
          <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <MapPin className="w-3 h-3 text-slate-400" />
            {item.location}
          </p>
        </div>
      ),
    },
    {
      id: "compensation",
      header: "Package (CTC)",
      sortable: true,
      cell: (item) => (
        <div className="text-xs">
          <span className="font-bold font-mono text-emerald-600 dark:text-emerald-400 text-sm">
            {formatLPA(item.ctcLpa)}
          </span>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Base: {formatLPA(item.baseSalaryLpa)}
          </p>
        </div>
      ),
    },
    {
      id: "eligibility",
      header: "Cutoff Criteria",
      cell: (item) => (
        <div className="text-xs space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-700 dark:text-slate-300">Min CGPA:</span>
            <strong className="font-mono text-slate-900 dark:text-white">{item.minCgpa.toFixed(1)}</strong>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <span>Max Backlogs: {item.maxBacklogs}</span>
          </div>
        </div>
      ),
    },
    {
      id: "skills",
      header: "Required Skills",
      cell: (item) => (
        <div className="flex flex-wrap gap-1 max-w-[200px]">
          {item.requiredSkills.map((s) => (
            <span
              key={s}
              className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
            >
              {s}
            </span>
          ))}
        </div>
      ),
    },
    {
      id: "vacancies",
      header: "Vacancies",
      sortable: true,
      cell: (item) => (
        <div className="text-xs">
          <span className="font-bold text-slate-900 dark:text-white">{item.vacancies}</span>
          <span className="text-slate-500 ml-1">open</span>
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (item) => (
        <Badge variant={item.status === "OPEN" ? "success" : "secondary"} dot>
          {item.status}
        </Badge>
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
            <span>Positions</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Job Positions & Employment Roles Catalog
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Designations, compensation structures, eligibility cutoffs, and required skill profiles across campus recruitment drives.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="primary" onClick={() => setShowModal(true)} className="gap-2 text-xs">
            <Plus className="w-4 h-4" />
            Add New Position
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Positions"
          value={positions.filter((p) => p.status === "OPEN").length}
          icon={<Layers className="w-5 h-5 text-indigo-500" />}
          description="Open for student applications"
        />
        <StatCard
          title="Total Vacancies"
          value={positions.reduce((sum, p) => sum + p.vacancies, 0)}
          icon={<Users className="w-5 h-5 text-emerald-500" />}
          description="Open employment slots"
        />
        <StatCard
          title="Full-time Roles"
          value={positions.filter((p) => p.employmentType === "FULL_TIME").length}
          icon={<Briefcase className="w-5 h-5 text-purple-500" />}
          description="Direct FTE appointments"
        />
        <StatCard
          title="Internship + FTE"
          value={positions.filter((p) => p.employmentType !== "FULL_TIME").length}
          icon={<Award className="w-5 h-5 text-amber-500" />}
          description="Pre-placement internships"
        />
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search title, company, skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>

          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Employment Types</option>
            <option value="FULL_TIME">Full Time Employment</option>
            <option value="INTERNSHIP">Internship</option>
            <option value="INTERN_PLUS_FTE">Internship + FTE</option>
          </Select>

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open Positions</option>
            <option value="CLOSED">Closed Positions</option>
          </Select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:bg-slate-900 dark:border-slate-800">
        <DataGrid
          data={filteredPositions}
          columns={columns}
          keyExtractor={(item) => item.id}
          loading={loading}
          paginated
          pageSize={10}
          emptyMessage="No job positions found matching the selected filters."
        />
      </div>

      {/* Create Position Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-bold text-white">Create New Job Position</h3>
            <p className="text-xs text-slate-400">
              Configure role compensation, academic eligibility thresholds, and skill tags.
            </p>

            <form onSubmit={handleCreatePosition} className="space-y-4 text-xs">
              <div>
                <label className="text-slate-300 font-medium">Link to Active Recruitment Drive *</label>
                <select
                  value={formData.driveId}
                  onChange={(e) => setFormData({ ...formData, driveId: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white text-xs"
                >
                  {drives.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.companyName} — {d.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">Position Title *</label>
                  <Input
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="e.g. Cloud Software Engineer"
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium">Department / Function</label>
                  <Input
                    value={formData.departmentFunction}
                    onChange={(e) => setFormData({ ...formData, departmentFunction: e.target.value })}
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">Employment Type</label>
                  <select
                    value={formData.employmentType}
                    onChange={(e) => setFormData({ ...formData, employmentType: e.target.value as EmploymentType })}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white text-xs"
                  >
                    <option value="FULL_TIME">Full Time</option>
                    <option value="INTERNSHIP">Internship</option>
                    <option value="INTERN_PLUS_FTE">Intern + FTE</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-300 font-medium">Location</label>
                  <Input
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium">Vacancies</label>
                  <Input
                    type="number"
                    value={formData.vacancies}
                    onChange={(e) => setFormData({ ...formData, vacancies: parseInt(e.target.value) || 1 })}
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">Total CTC (LPA) *</label>
                  <Input
                    type="number"
                    step="0.5"
                    value={formData.ctcLpa}
                    onChange={(e) => setFormData({ ...formData, ctcLpa: parseFloat(e.target.value) || 0 })}
                    className="mt-1 font-mono font-bold"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium">Base Salary (LPA)</label>
                  <Input
                    type="number"
                    step="0.5"
                    value={formData.baseSalaryLpa}
                    onChange={(e) => setFormData({ ...formData, baseSalaryLpa: parseFloat(e.target.value) || 0 })}
                    className="mt-1 font-mono"
                  />
                </div>
              </div>

              <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 space-y-3">
                <h4 className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
                  Mandatory Academic Eligibility Cutoffs
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-400">Minimum CGPA (10.0 scale)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.minCgpa}
                      onChange={(e) => setFormData({ ...formData, minCgpa: parseFloat(e.target.value) || 0 })}
                      className="mt-1 font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400">Maximum Allowed Active Backlogs</label>
                    <Input
                      type="number"
                      value={formData.maxBacklogs}
                      onChange={(e) => setFormData({ ...formData, maxBacklogs: parseInt(e.target.value) || 0 })}
                      className="mt-1 font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-slate-400">Required Skills (Comma separated)</label>
                  <Input
                    value={formData.requiredSkills}
                    onChange={(e) => setFormData({ ...formData, requiredSkills: e.target.value })}
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="ghost" size="sm" type="button" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit">
                  Save Position
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
