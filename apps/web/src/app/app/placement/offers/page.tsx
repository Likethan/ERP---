"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Award,
  Search,
  Plus,
  Building2,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  DollarSign,
  Briefcase,
  ChevronRight,
  Eye,
  AlertTriangle,
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
import { Offer, OfferStatus, Application } from "@/types/placement";

export default function OffersManagementPage() {
  const { showToast } = useToast();
  const [offers, setOffers] = useState<Offer[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    applicationId: "",
    employmentType: "FULL_TIME" as "FULL_TIME" | "INTERN_PLUS_FTE" | "INTERNSHIP",
    location: "Bengaluru, Karnataka",
    ctcLpa: 12.0,
    baseSalaryLpa: 10.0,
    variableLpa: 2.0,
    stipendMonthly: 0,
    joiningDate: "2027-07-01",
    responseDeadline: new Date(Date.now() + 10 * 86400000).toISOString().split("T")[0],
    releasedBy: "Placement Directorate",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [offersRes, appsRes] = await Promise.all([
        placementService.getOffers(),
        placementService.getApplications(),
      ]);
      if (offersRes.success && offersRes.data) {
        setOffers(offersRes.data);
      }
      if (appsRes.success && appsRes.data) {
        setApplications(appsRes.data);
      }
    } catch {
      showToast({
        title: "Error loading offers",
        message: "Failed to fetch corporate offers data",
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
  const filteredOffers = useMemo(() => {
    return offers.filter((o) => {
      const q = searchQuery.toLowerCase();
      const matchSearch =
        !q ||
        o.offerCode.toLowerCase().includes(q) ||
        o.studentName.toLowerCase().includes(q) ||
        o.rollNumber.toLowerCase().includes(q) ||
        o.companyName.toLowerCase().includes(q) ||
        o.positionTitle.toLowerCase().includes(q);

      const matchStatus = statusFilter === "ALL" || o.status === statusFilter;
      const matchType = typeFilter === "ALL" || o.employmentType === typeFilter;

      return matchSearch && matchStatus && matchType;
    });
  }, [offers, searchQuery, statusFilter, typeFilter]);

  // Derived statistics
  const stats = useMemo(() => {
    const total = offers.length;
    const accepted = offers.filter((o) => o.status === "ACCEPTED").length;
    const released = offers.filter((o) => o.status === "RELEASED").length;
    const declined = offers.filter((o) => o.status === "DECLINED").length;
    const rate = total > 0 ? Math.round((accepted / total) * 100) : 0;
    const totalCtc = offers.reduce((acc, curr) => acc + curr.ctcLpa, 0);
    const avgCtc = total > 0 ? (totalCtc / total).toFixed(2) : "0.00";
    const maxCtc = total > 0 ? Math.max(...offers.map((o) => o.ctcLpa)).toFixed(2) : "0.00";

    return { total, accepted, released, declined, rate, avgCtc, maxCtc };
  }, [offers]);

  // Available applications that can receive an offer
  const eligibleApps = useMemo(() => {
    return applications.filter(
      (a) =>
        a.status === "SHORTLISTED" ||
        a.status === "UNDER_REVIEW" ||
        a.status === "SUBMITTED" ||
        a.currentStage === "TECHNICAL" ||
        a.currentStage === "HR" ||
        a.currentStage === "FINAL" ||
        a.currentStage === "OFFER"
    );
  }, [applications]);

  const handleReleaseOffer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.applicationId) {
      showToast({
        title: "Validation Error",
        message: "Please select an applicant application record",
        type: "error",
      });
      return;
    }

    try {
      setSubmitting(true);
      const res = await placementService.releaseOffer(formData);
      if (res.success) {
        showToast({
          title: "Offer Released",
          message: `Official offer released for ${res.data?.studentName} at ${res.data?.companyName}`,
          type: "success",
        });
        setShowModal(false);
        await loadData();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to release offer";
      showToast({
        title: "Action Failed",
        message: msg,
        type: "error",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: OfferStatus) => {
    switch (status) {
      case "ACCEPTED":
        return (
          <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Accepted
          </Badge>
        );
      case "RELEASED":
        return (
          <Badge className="bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30 gap-1">
            <Clock className="w-3 h-3" />
            Released
          </Badge>
        );
      case "DECLINED":
        return (
          <Badge className="bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30 gap-1">
            <XCircle className="w-3 h-3" />
            Declined
          </Badge>
        );
      case "DRAFT":
        return (
          <Badge className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 gap-1">
            Draft
          </Badge>
        );
      case "EXPIRED":
        return (
          <Badge className="bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-500/30 gap-1">
            <AlertTriangle className="w-3 h-3" />
            Expired
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const columns: ColumnDef<Offer>[] = [
    {
      id: "offerCode",
      header: "Offer ID",
      accessorKey: "offerCode",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <Link
            href={`/app/placement/offers/${item.id}`}
            className="font-mono text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
          >
            {item.offerCode}
          </Link>
          <span className="text-[11px] text-muted-foreground">
            {item.employmentType.replace(/_/g, " ")}
          </span>
        </div>
      ),
    },
    {
      id: "student",
      header: "Candidate",
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
          <span className="text-xs text-muted-foreground font-mono">
            {item.rollNumber}
          </span>
        </div>
      ),
    },
    {
      id: "company",
      header: "Corporate Partner & Role",
      accessorKey: "companyName",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <Link
            href={`/app/placement/companies/${item.companyId}`}
            className="font-medium text-foreground hover:text-primary hover:underline flex items-center gap-1.5"
          >
            <Building2 className="w-3.5 h-3.5 text-muted-foreground" />
            {item.companyName}
          </Link>
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Briefcase className="w-3 h-3" />
            {item.positionTitle}
          </span>
        </div>
      ),
    },
    {
      id: "compensation",
      header: "Compensation (CTC)",
      accessorKey: "ctcLpa",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <span className="font-semibold text-foreground text-sm text-emerald-600 dark:text-emerald-400">
            {formatLPA(item.ctcLpa)}
          </span>
          <span className="text-[11px] text-muted-foreground">
            Base: {formatLPA(item.baseSalaryLpa)}
            {item.variableLpa ? ` + Var: ${formatLPA(item.variableLpa)}` : ""}
          </span>
        </div>
      ),
    },
    {
      id: "dates",
      header: "Offer & Response Deadline",
      accessorKey: "offerDate",
      sortable: true,
      cell: (item) => {
        const isExpiringSoon =
          item.status === "RELEASED" &&
          new Date(item.responseDeadline).getTime() - Date.now() < 3 * 86400000;
        return (
          <div className="flex flex-col">
            <span className="text-xs text-foreground flex items-center gap-1">
              <Calendar className="w-3 h-3 text-muted-foreground" />
              Released: {item.offerDate}
            </span>
            <span
              className={`text-[11px] flex items-center gap-1 ${
                isExpiringSoon ? "text-amber-500 font-medium" : "text-muted-foreground"
              }`}
            >
              <Clock className="w-3 h-3" />
              Deadline: {item.responseDeadline}
            </span>
          </div>
        );
      },
    },
    {
      id: "status",
      header: "Lifecycle Status",
      accessorKey: "status",
      sortable: true,
      cell: (item) => getStatusBadge(item.status),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (item) => (
        <div className="flex items-center gap-1.5 justify-end">
          <Link href={`/app/placement/offers/${item.id}`}>
            <Button variant="ghost" size="sm" className="h-8 gap-1 text-xs">
              <Eye className="w-3.5 h-3.5" />
              View
            </Button>
          </Link>
          <Link href={`/app/placement/offers/${item.id}`}>
            <Button variant="outline" size="sm" className="h-8 gap-1 text-xs">
              Review
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
              Offers & Compensation Management
            </h1>
            <Badge variant="outline" className="text-xs font-mono">
              Phase G
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Issue, track, and administer corporate job offers, CTC compensation packages, and candidate acceptances.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={() => setShowModal(true)}
            className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Release New Offer
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Offers Extended"
          value={stats.total}
          icon={<Award className="w-5 h-5 text-blue-500" />}
          description={`${stats.released} currently awaiting candidate response`}
        />
        <StatCard
          title="Offers Accepted"
          value={stats.accepted}
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-500" />}
          description={`${stats.rate}% overall candidate conversion rate`}
        />
        <StatCard
          title="Average CTC Offered"
          value={`₹${stats.avgCtc} LPA`}
          icon={<DollarSign className="w-5 h-5 text-purple-500" />}
          description={`Highest package recorded: ₹${stats.maxCtc} LPA`}
        />
        <StatCard
          title="Offers Declined / Expired"
          value={stats.declined}
          icon={<TrendingUp className="w-5 h-5 text-amber-500" />}
          description="Candidates opting for higher tiers / competitive offers"
        />
      </div>

      {/* Filters & Search Toolbar */}
      <div className="bg-card border rounded-xl p-4 shadow-sm flex flex-col md:flex-row items-stretch md:items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by student, roll number, company, role, or OFR-ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-36 h-9 text-xs"
            options={[
              { value: "ALL", label: "All Statuses" },
              { value: "RELEASED", label: "Released" },
              { value: "ACCEPTED", label: "Accepted" },
              { value: "DECLINED", label: "Declined" },
              { value: "DRAFT", label: "Draft" },
              { value: "EXPIRED", label: "Expired" },
            ]}
          />

          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="w-40 h-9 text-xs"
            options={[
              { value: "ALL", label: "All Contract Types" },
              { value: "FULL_TIME", label: "Full Time (FTE)" },
              { value: "INTERN_PLUS_FTE", label: "Intern + FTE" },
              { value: "INTERNSHIP", label: "Internship" },
            ]}
          />

          {(searchQuery || statusFilter !== "ALL" || typeFilter !== "ALL") && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearchQuery("");
                setStatusFilter("ALL");
                setTypeFilter("ALL");
              }}
              className="text-xs h-9"
            >
              Reset
            </Button>
          )}
        </div>
      </div>

      {/* DataGrid */}
      <div className="bg-card border rounded-xl shadow-sm overflow-hidden">
        <DataGrid<Offer>
          data={filteredOffers}
          columns={columns}
          keyExtractor={(item) => item.id}
          loading={loading}
          paginated={true}
          pageSize={10}
        />
      </div>

      {/* Release Offer Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-card border rounded-xl shadow-2xl max-w-xl w-full p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                  <Award className="w-5 h-5 text-primary" />
                  Release Corporate Job Offer
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Formalize a recruitment offer following successful interview rounds.
                </p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleReleaseOffer} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Select Applicant Application <span className="text-destructive">*</span>
                </label>
                <Select
                  value={formData.applicationId}
                  onChange={(e) => {
                    const selApp = applications.find((a) => a.id === e.target.value);
                    setFormData({
                      ...formData,
                      applicationId: e.target.value,
                      location: selApp?.companyName.includes("Bosch")
                        ? "Coimbatore, Tamil Nadu"
                        : "Bengaluru, Karnataka",
                    });
                  }}
                  className="w-full text-xs"
                  options={[
                    { value: "", label: "-- Choose Shortlisted Candidate Application --" },
                    ...eligibleApps.map((a) => ({
                      value: a.id,
                      label: `${a.studentName} (${a.rollNumber}) — ${a.companyName} [${a.positionTitle}]`,
                    })),
                  ]}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Employment Type
                  </label>
                  <Select
                    value={formData.employmentType}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        employmentType: e.target.value as "FULL_TIME" | "INTERN_PLUS_FTE" | "INTERNSHIP",
                      })
                    }
                    className="w-full text-xs"
                    options={[
                      { value: "FULL_TIME", label: "Full Time Employment (FTE)" },
                      { value: "INTERN_PLUS_FTE", label: "6M Intern + FTE Conversion" },
                      { value: "INTERNSHIP", label: "Summer Internship" },
                    ]}
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Work Location
                  </label>
                  <Input
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="h-9 text-xs"
                    placeholder="e.g. Bengaluru / Hyderabad / Pune"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Total CTC (LPA) <span className="text-destructive">*</span>
                  </label>
                  <Input
                    type="number"
                    step="0.1"
                    min="1"
                    max="100"
                    value={formData.ctcLpa}
                    onChange={(e) =>
                      setFormData({ ...formData, ctcLpa: parseFloat(e.target.value) || 0 })
                    }
                    className="h-9 text-xs font-semibold"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Base Salary (LPA)
                  </label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={formData.baseSalaryLpa}
                    onChange={(e) =>
                      setFormData({ ...formData, baseSalaryLpa: parseFloat(e.target.value) || 0 })
                    }
                    className="h-9 text-xs"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Variable (LPA)
                  </label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="50"
                    value={formData.variableLpa}
                    onChange={(e) =>
                      setFormData({ ...formData, variableLpa: parseFloat(e.target.value) || 0 })
                    }
                    className="h-9 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Anticipated Joining Date
                  </label>
                  <Input
                    type="date"
                    value={formData.joiningDate}
                    onChange={(e) => setFormData({ ...formData, joiningDate: e.target.value })}
                    className="h-9 text-xs"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Candidate Response Deadline <span className="text-destructive">*</span>
                  </label>
                  <Input
                    type="date"
                    value={formData.responseDeadline}
                    onChange={(e) =>
                      setFormData({ ...formData, responseDeadline: e.target.value })
                    }
                    className="h-9 text-xs"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Issuing Authority / Officer
                </label>
                <Input
                  value={formData.releasedBy}
                  onChange={(e) => setFormData({ ...formData, releasedBy: e.target.value })}
                  className="h-9 text-xs"
                />
              </div>

              <div className="bg-muted/40 p-3 rounded-lg text-xs space-y-1 border">
                <div className="font-semibold text-foreground flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5 text-primary" />
                  Autonomous Pipeline Progression
                </div>
                <p className="text-muted-foreground">
                  Releasing this offer will automatically advance the student&apos;s application stage to{" "}
                  <span className="font-semibold text-foreground">OFFER</span> and update their placement portfolio.
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={submitting}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground gap-1.5"
                >
                  {submitting ? "Issuing..." : "Confirm & Release Offer"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
