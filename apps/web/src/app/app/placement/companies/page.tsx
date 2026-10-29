"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Building2,
  Search,
  Plus,
  Globe,
  Users,
  Briefcase,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Award,
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
  Company,
  CompanyTier,
  CompanyStatus,
  CompanyType,
} from "@/types/placement";

export default function CompaniesDirectoryPage() {
  const { showToast } = useToast();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [tierFilter, setTierFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Onboard Company Modal
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    industry: "Information Technology & Software",
    companyType: "PRODUCT" as CompanyType,
    tier: "TIER_2_DREAM" as CompanyTier,
    website: "",
    headquarters: "Bengaluru, Karnataka",
    averageCtcLpa: 12.0,
    highestCtcLpa: 16.0,
    contactName: "",
    contactEmail: "",
    contactPhone: "",
    contactRole: "Campus Talent Lead",
    notes: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await placementService.getCompanies();
      setCompanies(res.data);
    } catch {
      showToast({
        title: "Error",
        message: "Failed to load corporate partners",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      showToast({
        title: "Validation Error",
        message: "Company name is required",
        type: "error",
      });
      return;
    }

    try {
      await placementService.createCompany({
        name: formData.name,
        code: formData.code || formData.name.slice(0, 6).toUpperCase(),
        industry: formData.industry,
        companyType: formData.companyType,
        tier: formData.tier,
        website: formData.website || "https://example.com",
        headquarters: formData.headquarters,
        averageCtcLpa: Number(formData.averageCtcLpa),
        highestCtcLpa: Number(formData.highestCtcLpa),
        contacts: formData.contactName
          ? [
              {
                id: `con-${Date.now()}`,
                name: formData.contactName,
                role: formData.contactRole,
                email: formData.contactEmail,
                phone: formData.contactPhone,
                isPrimary: true,
              },
            ]
          : [],
        notes: formData.notes,
      });

      showToast({
        title: "Success",
        message: `${formData.name} successfully onboarded`,
        type: "success",
      });
      setShowModal(false);
      loadData();
    } catch {
      showToast({
        title: "Error",
        message: "Failed to onboard company",
        type: "error",
      });
    }
  };

  const filteredCompanies = useMemo(() => {
    return companies.filter((c) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          c.name.toLowerCase().includes(q) ||
          c.code.toLowerCase().includes(q) ||
          c.industry.toLowerCase().includes(q) ||
          c.headquarters.toLowerCase().includes(q);
        if (!matches) return false;
      }

      if (tierFilter !== "ALL" && c.tier !== tierFilter) {
        return false;
      }

      if (statusFilter !== "ALL" && c.status !== statusFilter) {
        return false;
      }

      return true;
    });
  }, [companies, searchQuery, tierFilter, statusFilter]);

  const columns: ColumnDef<Company>[] = [
    {
      id: "company",
      header: "Corporate Partner",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <Link
            href={`/app/placement/companies/${item.id}`}
            className="font-medium text-slate-900 hover:text-indigo-600 dark:text-slate-100 dark:hover:text-indigo-400 transition-colors"
          >
            {item.name}
          </Link>
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            <span className="font-mono font-medium">{item.code}</span>
            <span>•</span>
            <span>{item.industry}</span>
          </div>
        </div>
      ),
    },
    {
      id: "tier",
      header: "Hiring Tier",
      sortable: true,
      cell: (item) => {
        const tierBadges: Record<
          CompanyTier,
          { label: string; color: string }
        > = {
          TIER_1_SUPER_DREAM: {
            label: "Super Dream (>₹15 LPA)",
            color:
              "bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border-purple-200",
          },
          TIER_2_DREAM: {
            label: "Dream (₹8 - ₹15 LPA)",
            color:
              "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200",
          },
          TIER_3_MASS: {
            label: "Mass / Core (<₹8 LPA)",
            color:
              "bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200",
          },
        };
        const t = tierBadges[item.tier] || tierBadges.TIER_2_DREAM;
        return (
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${t.color}`}
          >
            {t.label}
          </span>
        );
      },
    },
    {
      id: "compensation",
      header: "Average CTC / Highest",
      sortable: true,
      cell: (item) => (
        <div className="text-xs">
          <span className="font-bold font-mono text-slate-900 dark:text-white">
            {formatLPA(item.averageCtcLpa)}
          </span>
          <span className="text-slate-500 dark:text-slate-400 ml-1">avg</span>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Peak: {formatLPA(item.highestCtcLpa)}
          </p>
        </div>
      ),
    },
    {
      id: "hiring",
      header: "Hiring Record",
      cell: (item) => (
        <div className="text-xs text-slate-600 dark:text-slate-400">
          <p>
            <strong className="text-slate-900 dark:text-white">
              {item.totalHiredCount}
            </strong>{" "}
            Alumni Hired
          </p>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {item.activeDrivesCount} Active Drive(s)
          </p>
        </div>
      ),
    },
    {
      id: "contact",
      header: "Primary Contact",
      cell: (item) => {
        const contact =
          item.contacts.find((c) => c.isPrimary) || item.contacts[0];
        if (!contact)
          return <span className="text-xs text-slate-400">Not assigned</span>;
        return (
          <div className="text-xs">
            <span className="font-medium text-slate-900 dark:text-white">
              {contact.name}
            </span>
            <p className="text-[11px] text-slate-500 truncate max-w-[160px]">
              {contact.email}
            </p>
          </div>
        );
      },
    },
    {
      id: "status",
      header: "Status",
      cell: (item) => {
        if (item.status === "ACTIVE") {
          return (
            <Badge variant="success" dot>
              ACTIVE
            </Badge>
          );
        }
        if (item.status === "BLACKLISTED") {
          return (
            <Badge variant="destructive" dot>
              BLACKLISTED
            </Badge>
          );
        }
        return (
          <Badge variant="secondary" dot>
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
          <Link href={`/app/placement/companies/${item.id}`}>
            <Button variant="outline" size="sm" className="h-7 text-xs gap-1">
              Profile
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
            <span>Corporate Partners</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Corporate Partners & Recruiting Employers
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Enterprise directory of empanelled corporate recruiters, hiring
            tiers, historical hiring records, and campus HR contacts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            onClick={() => setShowModal(true)}
            className="gap-2 text-xs"
          >
            <Plus className="w-4 h-4" />
            Onboard New Partner
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Corporate Partners"
          value={companies.length}
          icon={<Building2 className="w-5 h-5 text-indigo-500" />}
          description="Active recruiting organizations"
        />
        <StatCard
          title="Super Dream Partners"
          value={
            companies.filter((c) => c.tier === "TIER_1_SUPER_DREAM").length
          }
          icon={<Award className="w-5 h-5 text-purple-500" />}
          description="Packages exceeding ₹15 LPA"
        />
        <StatCard
          title="Total Alumni Placed"
          value={companies.reduce((sum, c) => sum + c.totalHiredCount, 0)}
          icon={<Users className="w-5 h-5 text-emerald-500" />}
          description="Across all partner organizations"
        />
        <StatCard
          title="Active Campus Drives"
          value={companies.reduce((sum, c) => sum + c.activeDrivesCount, 0)}
          icon={<Briefcase className="w-5 h-5 text-amber-500" />}
          description="Current recruitment cycles"
        />
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search partner, industry, location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>

          <Select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Hiring Tiers</option>
            <option value="TIER_1_SUPER_DREAM">
              Super Dream (&gt;₹15 LPA)
            </option>
            <option value="TIER_2_DREAM">Dream (₹8 - ₹15 LPA)</option>
            <option value="TIER_3_MASS">Mass / Core (&lt;₹8 LPA)</option>
          </Select>

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Partner Statuses</option>
            <option value="ACTIVE">Active Partners</option>
            <option value="PROSPECT">Prospect Partners</option>
            <option value="BLACKLISTED">Blacklisted</option>
          </Select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:bg-slate-900 dark:border-slate-800">
        <DataGrid
          data={filteredCompanies}
          columns={columns}
          keyExtractor={(item) => item.id}
          loading={loading}
          paginated
          pageSize={10}
          emptyMessage="No corporate partners found matching the selected filters."
        />
      </div>

      {/* Onboard Company Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-bold text-white">
              Onboard Corporate Partner
            </h3>
            <p className="text-xs text-slate-400">
              Register a new corporate recruiter and assign placement tiers and
              primary HR contacts.
            </p>

            <form onSubmit={handleCreateCompany} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">
                    Company Name *
                  </label>
                  <Input
                    required
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    placeholder="e.g. Microsoft India"
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Partner Code
                  </label>
                  <Input
                    value={formData.code}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        code: e.target.value.toUpperCase(),
                      })
                    }
                    placeholder="e.g. MSFT"
                    className="mt-1 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">
                    Hiring Tier
                  </label>
                  <select
                    value={formData.tier}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        tier: e.target.value as CompanyTier,
                      })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white text-xs"
                  >
                    <option value="TIER_1_SUPER_DREAM">
                      Super Dream (&gt;₹15 LPA)
                    </option>
                    <option value="TIER_2_DREAM">Dream (₹8 - ₹15 LPA)</option>
                    <option value="TIER_3_MASS">
                      Mass / Core (&lt;₹8 LPA)
                    </option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Industry Domain
                  </label>
                  <Input
                    value={formData.industry}
                    onChange={(e) =>
                      setFormData({ ...formData, industry: e.target.value })
                    }
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">
                    Official Website
                  </label>
                  <Input
                    value={formData.website}
                    onChange={(e) =>
                      setFormData({ ...formData, website: e.target.value })
                    }
                    placeholder="https://..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Headquarters Location
                  </label>
                  <Input
                    value={formData.headquarters}
                    onChange={(e) =>
                      setFormData({ ...formData, headquarters: e.target.value })
                    }
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">
                    Expected Avg Package (LPA)
                  </label>
                  <Input
                    type="number"
                    step="0.5"
                    value={formData.averageCtcLpa}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        averageCtcLpa: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Peak Package (LPA)
                  </label>
                  <Input
                    type="number"
                    step="0.5"
                    value={formData.highestCtcLpa}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        highestCtcLpa: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
                <h4 className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
                  Campus HR Lead Contact
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="Contact Name"
                    value={formData.contactName}
                    onChange={(e) =>
                      setFormData({ ...formData, contactName: e.target.value })
                    }
                  />
                  <Input
                    placeholder="HR Email"
                    value={formData.contactEmail}
                    onChange={(e) =>
                      setFormData({ ...formData, contactEmail: e.target.value })
                    }
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  type="button"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit">
                  Onboard Partner
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
