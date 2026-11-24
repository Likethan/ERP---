"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { hodService } from "@/services/hod.service";
import { FacultyDetailView } from "@/types/domain";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Users,
  Search,
  Filter,
  ArrowRight,
  Mail,
  Phone,
  Clock,
  BookOpen,
  GraduationCap,
  Building,
  UserCheck,
  CheckCircle2,
  Calendar,
} from "lucide-react";

export default function HodFacultyPage() {
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [faculty, setFaculty] = useState<FacultyDetailView[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedDesignation, setSelectedDesignation] = useState("ALL");

  useEffect(() => {
    async function loadFaculty() {
      setLoading(true);
      try {
        const res = await hodService.getDepartmentFaculty({
          department: deptName,
          search: search.trim() || undefined,
          designation:
            selectedDesignation !== "ALL" ? selectedDesignation : undefined,
        });
        if (res.success && res.data) {
          // Strict department filter in frontend as defense-in-depth
          const filtered = res.data.filter(
            (f) =>
              f.department.toLowerCase().includes("computer") ||
              f.department.toLowerCase() === deptName.toLowerCase(),
          );
          setFaculty(filtered);
        }
      } catch (err) {
        console.error("Failed to load department faculty:", err);
      } finally {
        setLoading(false);
      }
    }
    loadFaculty();
  }, [deptName, search, selectedDesignation]);

  const designations = [
    "ALL",
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Lab Instructor",
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-yellow-100 text-yellow-950 border border-yellow-300">
              Department Faculty Roster
            </span>
            <span className="text-xs text-slate-500 font-mono">
              • {deptName}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Faculty Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Monitor instructional workloads, assigned subjects, and teaching
            performance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs px-2.5 py-1">
            Total Faculty: {faculty.length}
          </Badge>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <CardContent className="p-4 sm:p-5">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search faculty by name, employee code, or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-10 text-xs"
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Filter className="h-4 w-4 text-slate-400 shrink-0 hidden sm:block" />
              <select
                value={selectedDesignation}
                onChange={(e) => setSelectedDesignation(e.target.value)}
                aria-label="Filter by Designation"
                className="h-10 text-xs rounded-lg border border-slate-200 bg-white px-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-yellow-400 w-full sm:w-48 cursor-pointer"
              >
                {designations.map((d) => (
                  <option key={d} value={d}>
                    {d === "ALL" ? "All Designations" : d}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Faculty Directory Table / Cards */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="h-24 rounded-xl bg-white border border-slate-200 animate-pulse"
            />
          ))}
        </div>
      ) : faculty.length === 0 ? (
        <EmptyState
          icon={<Users className="h-10 w-10 text-slate-400" />}
          title="No Faculty Records Found"
          description={
            search
              ? `No faculty in ${deptName} match "${search}". Try adjusting your query.`
              : `No faculty records currently assigned to ${deptName}.`
          }
        />
      ) : (
        <div className="space-y-3">
          {faculty.map((f) => (
            <div
              key={f.id}
              className="p-4 sm:p-5 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 transition-all shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="flex items-start sm:items-center gap-3.5 min-w-0">
                <div className="h-11 w-11 rounded-xl bg-yellow-400 text-slate-950 font-bold text-sm flex items-center justify-center shrink-0 border border-yellow-500 shadow-xs">
                  {f.firstName[0]}
                  {f.lastName[0]}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-sm text-slate-900">
                      {f.firstName} {f.lastName}
                    </span>
                    <Badge variant="outline" className="font-mono text-[10px]">
                      {f.employeeCode}
                    </Badge>
                    <Badge
                      className={
                        f.status === "ACTIVE"
                          ? "bg-emerald-50 text-emerald-800 border-emerald-200 text-[10px]"
                          : "bg-slate-100 text-slate-600 text-[10px]"
                      }
                    >
                      {f.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5 flex items-center gap-3 flex-wrap">
                    <span className="font-medium text-slate-700">
                      {f.designation}
                    </span>
                    <span>•</span>
                    <span>{f.qualification}</span>
                    <span>•</span>
                    <span className="truncate">{f.specialization}</span>
                  </div>
                </div>
              </div>

              {/* Workload and Contact Pill */}
              <div className="flex flex-wrap items-center gap-3 sm:gap-4 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-slate-100">
                <div className="text-right">
                  <div className="text-xs font-bold font-mono text-slate-900">
                    {f.teachingLoadHours} hrs/week
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {f.assignedSubjects?.length || 0} Subjects Assigned
                  </div>
                </div>

                <div className="text-right hidden sm:block">
                  <div className="text-xs text-slate-700 flex items-center gap-1 font-mono">
                    <Mail className="h-3 w-3 text-slate-400" />
                    {f.email}
                  </div>
                  <div className="text-[10px] text-slate-500 flex items-center gap-1 justify-end font-mono">
                    <Phone className="h-3 w-3 text-slate-400" />
                    {f.phone}
                  </div>
                </div>

                <Link href={`/hod/faculty/${f.id}`}>
                  <Button
                    variant="outline"
                    size="sm"
                    className="hover:bg-yellow-400 hover:text-slate-950 hover:border-yellow-500 text-xs gap-1 font-semibold"
                  >
                    View 360° Profile
                    <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
