"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Award,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Building2,
  Calendar,
  Download,
  Users,
  DollarSign,
  TrendingUp,
  UserCheck,
  Briefcase,
  ChevronRight,
  ShieldCheck,
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
import { formatLPA } from "@/services/placement-calculator";
import {
  PlacementOutcome,
  PlacementStatus,
  StudentPlacementProfile,
} from "@/types/placement";

export default function PlacementOutcomesPage() {
  const { showToast } = useToast();
  const [outcomes, setOutcomes] = useState<PlacementOutcome[]>([]);
  const [profiles, setProfiles] = useState<StudentPlacementProfile[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [deptFilter, setDeptFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Outcome Confirmation Modal
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [selectedOutcome, setSelectedOutcome] =
    useState<PlacementOutcome | null>(null);
  const [confirmData, setConfirmData] = useState({
    companyName: "",
    positionTitle: "",
    ctcLpa: 12.0,
    joiningDate: "2027-07-01",
    status: "PLACED" as PlacementStatus,
    notes: "Verified with corporate signing and student acceptance letter",
  });
  const [processing, setProcessing] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [outRes, profRes] = await Promise.all([
        placementService.getPlacementOutcomes(),
        placementService.getPlacementStudents(),
      ]);
      if (outRes.success && outRes.data) {
        setOutcomes(outRes.data);
      }
      if (profRes.success && profRes.data) {
        setProfiles(profRes.data);
      }
    } catch {
      showToast({
        title: "Error loading outcomes",
        message: "Failed to fetch student placement records",
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
  const filteredOutcomes = useMemo(() => {
    return outcomes.filter((o) => {
      const q = searchQuery.toLowerCase();
      const matchSearch =
        !q ||
        o.studentName.toLowerCase().includes(q) ||
        o.rollNumber.toLowerCase().includes(q) ||
        (o.companyName && o.companyName.toLowerCase().includes(q)) ||
        (o.positionTitle && o.positionTitle.toLowerCase().includes(q));

      const matchDept = deptFilter === "ALL" || o.department === deptFilter;
      const matchStatus = statusFilter === "ALL" || o.status === statusFilter;

      return matchSearch && matchDept && matchStatus;
    });
  }, [outcomes, searchQuery, deptFilter, statusFilter]);

  // Derived statistics
  const stats = useMemo(() => {
    const total = outcomes.length;
    const placed = outcomes.filter((o) => o.status === "PLACED").length;
    const inProcess = outcomes.filter((o) => o.status === "IN_PROCESS").length;
    const notPlaced = outcomes.filter((o) => o.status === "NOT_PLACED").length;
    const rate = total > 0 ? Math.round((placed / total) * 100) : 0;

    const placedPackages = outcomes.filter(
      (o) => o.status === "PLACED" && o.ctcLpa > 0,
    );
    const totalCtc = placedPackages.reduce((acc, curr) => acc + curr.ctcLpa, 0);
    const avgCtc =
      placedPackages.length > 0
        ? (totalCtc / placedPackages.length).toFixed(2)
        : "0.00";
    const maxCtc =
      placedPackages.length > 0
        ? Math.max(...placedPackages.map((o) => o.ctcLpa)).toFixed(2)
        : "0.00";

    return { total, placed, inProcess, notPlaced, rate, avgCtc, maxCtc };
  }, [outcomes]);

  const handleOpenConfirmModal = (item: PlacementOutcome) => {
    setSelectedOutcome(item);
    setConfirmData({
      companyName: item.companyName || "Cisco Systems",
      positionTitle: item.positionTitle || "Software Engineer",
      ctcLpa: item.ctcLpa || 15.0,
      joiningDate: item.joiningDate || "2027-07-01",
      status: "PLACED",
      notes:
        item.notes || "Official placement confirmed by Placement Directorate",
    });
    setShowConfirmModal(true);
  };

  const handleSaveOutcome = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOutcome) return;

    try {
      setProcessing(true);
      const res = await placementService.confirmPlacementOutcome({
        studentId: selectedOutcome.studentId,
        companyName: confirmData.companyName,
        positionTitle: confirmData.positionTitle,
        ctcLpa: confirmData.ctcLpa,
        joiningDate: confirmData.joiningDate,
        status: confirmData.status,
        notes: confirmData.notes,
        confirmedBy: "Placement Director",
      });

      if (res.success) {
        showToast({
          title: "Outcome Confirmed",
          message: `Placement record successfully recorded for ${selectedOutcome.studentName}`,
          type: "success",
        });
        setShowConfirmModal(false);
        await loadData();
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to record outcome";
      showToast({
        title: "Action Failed",
        message: msg,
        type: "error",
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleExportCSV = () => {
    const headers = [
      "Student ID",
      "Student Name",
      "Roll Number",
      "Department",
      "Program",
      "Graduation Year",
      "Placement Status",
      "Company",
      "Position",
      "CTC (LPA)",
      "Joining Date",
      "Confirmed At",
      "Confirmed By",
    ];

    const rows = filteredOutcomes.map((o) => [
      `"${o.studentId}"`,
      `"${o.studentName}"`,
      `"${o.rollNumber}"`,
      `"${o.department}"`,
      `"${o.program}"`,
      o.graduationYear,
      o.status,
      `"${o.companyName || "N/A"}"`,
      `"${o.positionTitle || "N/A"}"`,
      o.ctcLpa || 0,
      `"${o.joiningDate || "N/A"}"`,
      `"${o.confirmedAt || "N/A"}"`,
      `"${o.confirmedBy || "N/A"}"`,
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `CampusOS_Placement_Outcomes_${new Date().toISOString().split("T")[0]}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast({
      title: "Export Completed",
      message: "Placement outcomes ledger exported to CSV successfully",
      type: "success",
    });
  };

  const getStatusBadge = (status: PlacementStatus) => {
    switch (status) {
      case "PLACED":
        return (
          <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 gap-1 font-medium">
            <CheckCircle2 className="w-3 h-3" />
            Placed
          </Badge>
        );
      case "IN_PROCESS":
        return (
          <Badge className="bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30 gap-1 font-medium">
            <Clock className="w-3 h-3" />
            In Process
          </Badge>
        );
      case "NOT_PLACED":
        return (
          <Badge className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 gap-1 font-medium">
            <AlertCircle className="w-3 h-3" />
            Not Placed
          </Badge>
        );
      case "WITHDRAWN":
        return (
          <Badge className="bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-500/30 gap-1 font-medium">
            <XCircle className="w-3 h-3" />
            Withdrawn
          </Badge>
        );
      case "DEFERRED":
        return (
          <Badge className="bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30 gap-1 font-medium">
            Deferred
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const columns: ColumnDef<PlacementOutcome>[] = [
    {
      id: "student",
      header: "Student Candidate",
      accessorKey: "studentName",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <Link
            href={`/app/placement/students/${item.studentId}`}
            className="font-medium text-foreground hover:text-primary hover:underline"
          >
            {item.studentName}
          </Link>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="font-mono">{item.rollNumber}</span>
            <span>•</span>
            <span>{item.department}</span>
          </div>
        </div>
      ),
    },
    {
      id: "program",
      header: "Program & Batch",
      accessorKey: "program",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col text-xs">
          <span className="font-medium text-foreground">{item.program}</span>
          <span className="text-muted-foreground">
            Class of {item.graduationYear}
          </span>
        </div>
      ),
    },
    {
      id: "companyRole",
      header: "Corporate Destination",
      accessorKey: "companyName",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          {item.companyName ? (
            <>
              <span className="font-medium text-foreground flex items-center gap-1.5 text-xs">
                <Building2 className="w-3.5 h-3.5 text-primary" />
                {item.companyName}
              </span>
              <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                <Briefcase className="w-3 h-3" />
                {item.positionTitle || "Appointed Role"}
              </span>
            </>
          ) : (
            <span className="text-xs text-muted-foreground italic">
              No company assigned
            </span>
          )}
        </div>
      ),
    },
    {
      id: "ctc",
      header: "Package (CTC)",
      accessorKey: "ctcLpa",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          {item.ctcLpa > 0 ? (
            <span className="font-semibold text-xs text-emerald-600 dark:text-emerald-400">
              {formatLPA(item.ctcLpa)}
            </span>
          ) : (
            <span className="text-xs text-muted-foreground">—</span>
          )}
          {item.joiningDate && (
            <span className="text-[10px] text-muted-foreground flex items-center gap-1">
              <Calendar className="w-2.5 h-2.5" />
              Join: {item.joiningDate}
            </span>
          )}
        </div>
      ),
    },
    {
      id: "status",
      header: "Placement Status",
      accessorKey: "status",
      sortable: true,
      cell: (item) => getStatusBadge(item.status),
    },
    {
      id: "confirmed",
      header: "Audit Confirmation",
      accessorKey: "confirmedBy",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col text-[11px]">
          {item.confirmedBy ? (
            <>
              <span className="text-foreground flex items-center gap-1 font-medium">
                <ShieldCheck className="w-3 h-3 text-emerald-500" />
                {item.confirmedBy}
              </span>
              <span className="text-muted-foreground">
                {item.confirmedAt
                  ? new Date(item.confirmedAt).toLocaleDateString()
                  : ""}
              </span>
            </>
          ) : (
            <span className="text-muted-foreground italic">Unconfirmed</span>
          )}
        </div>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (item) => (
        <div className="flex items-center gap-1.5 justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleOpenConfirmModal(item)}
            className="h-8 gap-1 text-xs"
          >
            Update Outcome
          </Button>
          <Link href={`/app/placement/students/${item.studentId}`}>
            <Button variant="ghost" size="sm" className="h-8 gap-1 text-xs">
              Profile
              <ChevronRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Placement Outcomes Ledger
            </h1>
            <Badge variant="outline" className="text-xs font-mono">
              Phase H
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Institutional ledger of final graduate appointments, corporate
            placements, and verified CTC compensation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleExportCSV}
            className="gap-2 text-xs h-9"
          >
            <Download className="w-4 h-4" />
            Export Outcomes (CSV)
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Graduating Cohort"
          value={stats.total}
          icon={<Users className="w-5 h-5 text-blue-500" />}
          description="Total enrolled final-year candidates in 2026-2027 batch"
        />
        <StatCard
          title="Placed Graduates"
          value={stats.placed}
          icon={<UserCheck className="w-5 h-5 text-emerald-500" />}
          description={`${stats.rate}% institutional placement conversion rate`}
        />
        <StatCard
          title="Average Placement Package"
          value={`₹${stats.avgCtc} LPA`}
          icon={<DollarSign className="w-5 h-5 text-purple-500" />}
          description="Average fixed and variable package for placed candidates"
        />
        <StatCard
          title="Highest Package"
          value={`₹${stats.maxCtc} LPA`}
          icon={<Award className="w-5 h-5 text-amber-500" />}
          description="Top corporate CTC secured across all departments"
        />
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-card border rounded-xl p-4 shadow-sm flex flex-col md:flex-row items-stretch md:items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by student, roll number, corporate partner, or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            className="w-44 h-9 text-xs"
            options={[
              { value: "ALL", label: "All Departments" },
              {
                value: "Computer Science and Engineering",
                label: "Computer Science (CSE)",
              },
              {
                value: "Electronics & Communication Engineering",
                label: "Electronics (ECE)",
              },
              { value: "Mechanical Engineering", label: "Mechanical" },
              { value: "Information Technology", label: "Information Tech" },
            ]}
          />

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-36 h-9 text-xs"
            options={[
              { value: "ALL", label: "All Statuses" },
              { value: "PLACED", label: "Placed" },
              { value: "IN_PROCESS", label: "In Process" },
              { value: "NOT_PLACED", label: "Not Placed" },
              { value: "WITHDRAWN", label: "Withdrawn" },
              { value: "DEFERRED", label: "Deferred" },
            ]}
          />

          {(searchQuery || deptFilter !== "ALL" || statusFilter !== "ALL") && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearchQuery("");
                setDeptFilter("ALL");
                setStatusFilter("ALL");
              }}
              className="text-xs h-9"
            >
              Reset
            </Button>
          )}
        </div>
      </div>

      {/* Outcomes DataGrid */}
      <div className="bg-card border rounded-xl shadow-sm overflow-hidden">
        <DataGrid<PlacementOutcome>
          data={filteredOutcomes}
          columns={columns}
          keyExtractor={(item) => item.id}
          loading={loading}
          paginated={true}
          pageSize={10}
        />
      </div>

      {/* Update Outcome Modal */}
      {showConfirmModal && selectedOutcome && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-card border rounded-xl shadow-2xl max-w-lg w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-primary" />
                  Record Placement Outcome
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Confirm official institutional outcome for{" "}
                  {selectedOutcome.studentName} ({selectedOutcome.rollNumber})
                </p>
              </div>
              <button
                onClick={() => setShowConfirmModal(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveOutcome} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Placement Status <span className="text-destructive">*</span>
                  </label>
                  <Select
                    value={confirmData.status}
                    onChange={(e) =>
                      setConfirmData({
                        ...confirmData,
                        status: e.target.value as PlacementStatus,
                      })
                    }
                    className="w-full text-xs"
                    options={[
                      { value: "PLACED", label: "Placed (Confirmed)" },
                      {
                        value: "IN_PROCESS",
                        label: "In Process / Interviewing",
                      },
                      { value: "NOT_PLACED", label: "Not Placed" },
                      {
                        value: "WITHDRAWN",
                        label: "Withdrawn from Placements",
                      },
                      { value: "DEFERRED", label: "Deferred (Higher Studies)" },
                    ]}
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Appointed Company
                  </label>
                  <Input
                    value={confirmData.companyName}
                    onChange={(e) =>
                      setConfirmData({
                        ...confirmData,
                        companyName: e.target.value,
                      })
                    }
                    className="h-9 text-xs"
                    placeholder="e.g. Cisco Systems"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Position Title / Role
                  </label>
                  <Input
                    value={confirmData.positionTitle}
                    onChange={(e) =>
                      setConfirmData({
                        ...confirmData,
                        positionTitle: e.target.value,
                      })
                    }
                    className="h-9 text-xs"
                    placeholder="e.g. Software Engineer"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Package (CTC in LPA)
                  </label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={confirmData.ctcLpa}
                    onChange={(e) =>
                      setConfirmData({
                        ...confirmData,
                        ctcLpa: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="h-9 text-xs"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Expected Joining Date
                </label>
                <Input
                  type="date"
                  value={confirmData.joiningDate}
                  onChange={(e) =>
                    setConfirmData({
                      ...confirmData,
                      joiningDate: e.target.value,
                    })
                  }
                  className="h-9 text-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Directorate Verification Notes
                </label>
                <textarea
                  rows={2}
                  value={confirmData.notes}
                  onChange={(e) =>
                    setConfirmData({ ...confirmData, notes: e.target.value })
                  }
                  className="w-full text-xs p-2 rounded-lg border bg-background text-foreground"
                  placeholder="e.g. Verified with signed acceptance letter"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowConfirmModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={processing}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground"
                >
                  {processing ? "Saving..." : "Record & Verify Outcome"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
