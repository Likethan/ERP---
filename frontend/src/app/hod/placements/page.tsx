"use client";

import React, { useEffect, useState } from "react";
import {
  Briefcase,
  TrendingUp,
  Award,
  Users,
  Building2,
  DollarSign,
  Search,
  Filter,
  Download,
  CheckCircle2,
  Clock,
  ChevronRight,
  ExternalLink,
  GraduationCap,
} from "lucide-react";
import {
  hodService,
  HodPlacementOverview,
  HodStudentPlacementItem,
  HodPlacementsData,
} from "@/services/hod.service";
import { useToast } from "@/components/ui/toast";

export default function HodPlacementsPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<HodPlacementOverview | null>(null);
  const [studentsData, setStudentsData] = useState<HodPlacementsData | null>(
    null,
  );
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [sectionFilter, setSectionFilter] = useState("ALL");
  const [companyFilter, setCompanyFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const [ovRes, stRes] = await Promise.all([
        hodService.getPlacementOverview(),
        hodService.getPlacementStudents(
          statusFilter,
          sectionFilter,
          companyFilter,
        ),
      ]);
      if (ovRes.data) setOverview(ovRes.data);
      if (stRes.data) setStudentsData(stRes.data);
    } catch {
      addToast({
        title: "Error Loading Data",
        description: "Failed to retrieve placement and internship statistics.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter, sectionFilter, companyFilter]);

  const filteredStudents = (studentsData?.students || []).filter((s) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      s.name.toLowerCase().includes(q) ||
      s.registerNumber.includes(q) ||
      (s.company && s.company.toLowerCase().includes(q)) ||
      (s.role && s.role.toLowerCase().includes(q))
    );
  });

  const exportCsv = () => {
    if (!filteredStudents.length) return;
    const headers = [
      "Register Number",
      "Student Name",
      "Year",
      "Section",
      "CGPA",
      "Placement Status",
      "Company",
      "Role",
      "Package (LPA)",
      "Selection Date",
      "Internship Status",
      "Internship Company",
      "Monthly Stipend",
    ];
    const rows = filteredStudents.map((s) => [
      s.registerNumber,
      `"${s.name}"`,
      s.year,
      s.section,
      s.cgpa,
      s.placementStatus,
      `"${s.company || "N/A"}"`,
      `"${s.role || "N/A"}"`,
      s.packageLpa || "",
      s.selectionDate || "",
      s.internshipStatus,
      `"${s.internshipCompany || "N/A"}"`,
      s.stipendMonthly || "",
    ]);
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `CSE_Placement_Roster_${new Date().toISOString().slice(0, 10)}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    addToast({
      title: "Export Completed",
      description: "Placement roster CSV downloaded.",
      variant: "success",
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PLACED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="h-3 w-3" /> Placed
          </span>
        );
      case "INTERVIEW":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200">
            Interviewing
          </span>
        );
      case "ELIGIBLE":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 border border-amber-200">
            Eligible
          </span>
        );
      case "INTERNSHIP":
      case "INTERNSHIP_COMPLETED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-semibold text-purple-700 border border-purple-200">
            Internship
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Placement & Internship Monitoring
            </h1>
            <span className="rounded-md bg-yellow-100 px-2.5 py-0.5 text-xs font-bold text-yellow-800 border border-yellow-300">
              Graduating Batch 2026
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Comprehensive oversight of corporate drives, packages, offers, and
            internship conversions.
          </p>
        </div>

        <button
          onClick={exportCsv}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50"
        >
          <Download className="h-4 w-4" />
          Export Roster (CSV)
        </button>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-6">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Eligible Final Years
            </span>
            <Users className="h-4 w-4 text-slate-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {overview?.placementEligible || 172}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Out of 180 cohort
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Students Placed
            </span>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-600">
            {overview?.studentsPlaced || 151}
          </div>
          <div className="mt-1 text-[11px] text-emerald-600/80 font-medium">
            Offers Accepted
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Placement Rate
            </span>
            <TrendingUp className="h-4 w-4 text-yellow-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {overview?.placementPercentage || 87.8}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            +3.3% vs last year
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Highest Package
            </span>
            <Award className="h-4 w-4 text-amber-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-600">
            ₹{overview?.highestPackageLpa || 24.5}{" "}
            <span className="text-xs font-normal">LPA</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-500">AWS Cloud Role</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Average CTC
            </span>
            <DollarSign className="h-4 w-4 text-blue-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            ₹{overview?.averagePackageLpa || 6.8}{" "}
            <span className="text-xs font-normal">LPA</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Median: ₹5.5 LPA
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Paid Internships
            </span>
            <Briefcase className="h-4 w-4 text-purple-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-purple-600">
            {overview?.internshipParticipants || 138}
          </div>
          <div className="mt-1 text-[11px] text-purple-600/80 font-medium">
            Stipend Active
          </div>
        </div>
      </div>

      {/* Top Recruiters & Package Distribution */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Top Corporate Recruiters */}
        <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <h2 className="text-sm font-bold text-slate-900 flex items-center justify-between">
            <span>Corporate Recruiters & Offers Breakdown</span>
            <span className="text-xs font-normal text-slate-500">
              Total 166 Department Offers
            </span>
          </h2>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {(overview?.topRecruiters || []).map((rec, i) => (
              <div
                key={i}
                className="rounded-lg border border-slate-100 bg-slate-50/70 p-3 hover:border-yellow-300 transition-colors"
              >
                <div className="text-xs font-bold text-slate-900 truncate">
                  {rec.company}
                </div>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="text-lg font-bold text-slate-900">
                    {rec.offers}
                  </span>
                  <span className="text-[10px] text-slate-500">Offers</span>
                </div>
                <div className="mt-1 text-[10px] text-slate-500 truncate">
                  {rec.tier}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Salary Ranges */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <h2 className="text-sm font-bold text-slate-900">
            Salary Package Tiers
          </h2>
          <div className="mt-4 space-y-3">
            {(overview?.packageRanges || []).map((range, i) => (
              <div key={i}>
                <div className="flex items-center justify-between text-xs font-medium text-slate-700">
                  <span>{range.range}</span>
                  <span className="font-bold text-slate-900">
                    {range.count} ({range.percentage}%)
                  </span>
                </div>
                <div className="mt-1.5 h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-yellow-400"
                    style={{ width: `${range.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-xs sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by student name, roll number, company, or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-200 pl-9 pr-4 py-2 text-sm focus:border-yellow-400 focus:outline-hidden focus:ring-1 focus:ring-yellow-400"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700"
          >
            <option value="ALL">All Statuses</option>
            <option value="PLACED">Placed</option>
            <option value="INTERVIEW">In Interview</option>
            <option value="ELIGIBLE">Eligible</option>
          </select>

          <select
            value={sectionFilter}
            onChange={(e) => setSectionFilter(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700"
          >
            <option value="ALL">All Sections</option>
            <option value="A">Section A</option>
            <option value="B">Section B</option>
            <option value="C">Section C</option>
          </select>
        </div>
      </div>

      {/* Student Placement Roster Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
        <div className="border-b border-slate-200 px-5 py-3.5 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            Student Placement & Internship Ledger ({filteredStudents.length})
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            Department of Computer Science & Engineering
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-slate-500">
            Loading placement records...
          </div>
        ) : filteredStudents.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">
            No students found matching current filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
                <tr>
                  <th className="px-5 py-3">Student Name & Roll No</th>
                  <th className="px-4 py-3">Year / Sec</th>
                  <th className="px-4 py-3 text-center">CGPA</th>
                  <th className="px-4 py-3">Company & Job Role</th>
                  <th className="px-4 py-3 text-right">Package</th>
                  <th className="px-4 py-3 text-center">Placement Status</th>
                  <th className="px-5 py-3">Internship Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredStudents.map((st) => (
                  <tr
                    key={st.registerNumber}
                    className="hover:bg-yellow-50/40 transition-colors"
                  >
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-900 text-sm">
                        {st.name}
                      </div>
                      <div className="text-[11px] font-mono text-slate-500">
                        {st.registerNumber}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="font-medium text-slate-800">
                        {st.year}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        Section {st.section}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-center font-bold text-slate-900">
                      {st.cgpa.toFixed(2)}
                    </td>
                    <td className="px-4 py-3.5">
                      {st.company ? (
                        <>
                          <div className="font-semibold text-slate-900">
                            {st.company}
                          </div>
                          <div className="text-[11px] text-slate-500">
                            {st.role || "Technical Role"}
                          </div>
                        </>
                      ) : (
                        <span className="text-slate-400 italic">
                          Awaiting Selection
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-right font-mono font-bold text-slate-900">
                      {st.packageLpa ? (
                        <span className="text-emerald-700">
                          ₹{st.packageLpa} LPA
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      {getStatusBadge(st.placementStatus)}
                    </td>
                    <td className="px-5 py-3.5">
                      {st.internshipCompany ? (
                        <div>
                          <span className="font-semibold text-slate-800">
                            {st.internshipCompany}
                          </span>
                          <span className="text-[11px] text-slate-500 block">
                            {st.internshipDuration} • ₹{st.stipendMonthly}/mo
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400 text-[11px]">
                          {st.internshipStatus}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
