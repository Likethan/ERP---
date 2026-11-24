"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { hodService } from "@/services/hod.service";
import { StudentComprehensiveDetail } from "@/types/domain";
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
  GraduationCap,
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Users,
} from "lucide-react";

export default function HodStudentsPage() {
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [students, setStudents] = useState<StudentComprehensiveDetail[]>([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [semester, setSemester] = useState<string>("ALL");
  const [section, setSection] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [page, setPage] = useState(1);
  const pageSize = 12;

  useEffect(() => {
    async function loadStudents() {
      setLoading(true);
      try {
        const res = await hodService.getDepartmentStudents(
          {
            search: search.trim() || undefined,
            semester: semester !== "ALL" ? Number(semester) : undefined,
            section: section !== "ALL" ? section : undefined,
            status: statusFilter !== "ALL" ? statusFilter : undefined,
            page,
            pageSize,
          },
          deptName,
        );

        if (res.success && res.data) {
          // Strict department filter on frontend as defense-in-depth
          const deptFiltered = res.data.filter(
            (s) =>
              s.program.department.toLowerCase().includes("computer") ||
              s.program.department.toLowerCase() === deptName.toLowerCase(),
          );
          setStudents(deptFiltered);
          setTotalRecords(res.pagination?.totalRecords || deptFiltered.length);
        }
      } catch (err) {
        console.error("Failed to load department students:", err);
      } finally {
        setLoading(false);
      }
    }
    loadStudents();
  }, [deptName, search, semester, section, statusFilter, page]);

  const totalPages = Math.ceil(totalRecords / pageSize) || 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-yellow-100 text-yellow-950 border border-yellow-300">
              Department Student Roster
            </span>
            <span className="text-xs text-slate-500 font-mono">
              • {deptName}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Student Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Monitor student profiles, academic performance (CGPA/backlogs), and
            attendance compliance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs px-2.5 py-1">
            Enrolled Students: {totalRecords}
          </Badge>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <CardContent className="p-4 sm:p-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Search */}
            <div className="relative w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search by name, roll no, reg no..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="pl-9 h-10 text-xs"
              />
            </div>

            {/* Semester Filter */}
            <div>
              <select
                value={semester}
                onChange={(e) => {
                  setSemester(e.target.value);
                  setPage(1);
                }}
                aria-label="Filter by Semester"
                className="h-10 text-xs rounded-lg border border-slate-200 bg-white px-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-yellow-400 w-full cursor-pointer"
              >
                <option value="ALL">All Semesters</option>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Section Filter */}
            <div>
              <select
                value={section}
                onChange={(e) => {
                  setSection(e.target.value);
                  setPage(1);
                }}
                aria-label="Filter by Section"
                className="h-10 text-xs rounded-lg border border-slate-200 bg-white px-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-yellow-400 w-full cursor-pointer"
              >
                <option value="ALL">All Sections</option>
                <option value="A">Section A</option>
                <option value="B">Section B</option>
                <option value="C">Section C</option>
                <option value="D">Section D</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                aria-label="Filter by Status"
                className="h-10 text-xs rounded-lg border border-slate-200 bg-white px-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-yellow-400 w-full cursor-pointer"
              >
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="ADMITTED">ADMITTED</option>
                <option value="ON_LEAVE">ON LEAVE</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Student Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-3">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="h-12 rounded-lg bg-slate-100 animate-pulse"
                />
              ))}
            </div>
          ) : students.length === 0 ? (
            <div className="p-8">
              <EmptyState
                icon={<GraduationCap className="h-10 w-10 text-slate-400" />}
                title="No Students Matching Query"
                description={`No students in ${deptName} match the selected filters.`}
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="p-3.5">Roll No & Reg No</th>
                    <th className="p-3.5">Student Name</th>
                    <th className="p-3.5">Sem / Section</th>
                    <th className="p-3.5">Batch</th>
                    <th className="p-3.5 text-center">Attendance %</th>
                    <th className="p-3.5 text-center">CGPA</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {students.map((stu) => {
                    const att = stu.attendanceSummary.overallPercentage;
                    const isShortage = att < 75;

                    return (
                      <tr
                        key={stu.id}
                        className="hover:bg-yellow-50/30 transition-colors"
                      >
                        <td className="p-3.5">
                          <div className="font-mono font-bold text-slate-900">
                            {stu.rollNumber}
                          </div>
                          <div className="font-mono text-[10px] text-slate-400">
                            {stu.registrationNumber}
                          </div>
                        </td>
                        <td className="p-3.5">
                          <div className="font-bold text-slate-900">
                            {stu.firstName} {stu.lastName}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono truncate max-w-xs">
                            {stu.email}
                          </div>
                        </td>
                        <td className="p-3.5 font-mono">
                          Sem {stu.currentSemester} — Sec {stu.section}
                        </td>
                        <td className="p-3.5 font-mono text-slate-600">
                          {stu.batch}
                        </td>
                        <td className="p-3.5 text-center">
                          <div className="inline-flex items-center gap-1 font-mono font-bold">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] ${
                                att >= 75
                                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                  : att >= 65
                                    ? "bg-amber-50 text-amber-800 border border-amber-200"
                                    : "bg-rose-50 text-rose-800 border border-rose-200"
                              }`}
                            >
                              {att}%
                            </span>
                            {isShortage && (
                              <span title="Attendance Shortage">
                                <ShieldAlert className="h-3.5 w-3.5 text-rose-600 shrink-0" />
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-3.5 text-center font-mono font-bold text-slate-900">
                          {stu.academicStats.cgpa}
                        </td>
                        <td className="p-3.5">
                          <Badge
                            className={
                              stu.status === "ACTIVE"
                                ? "bg-emerald-50 text-emerald-800 border-emerald-200 text-[10px]"
                                : "bg-slate-100 text-slate-600 text-[10px]"
                            }
                          >
                            {stu.status}
                          </Badge>
                        </td>
                        <td className="p-3.5 text-right">
                          <Link href={`/hod/students/${stu.id}`}>
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-xs hover:bg-yellow-400 hover:text-slate-950 hover:border-yellow-500 font-semibold gap-1"
                            >
                              Profile
                              <ArrowRight className="h-3 w-3" />
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t border-slate-200 text-xs">
              <span className="text-slate-500">
                Page{" "}
                <span className="font-bold text-slate-900 font-mono">
                  {page}
                </span>{" "}
                of{" "}
                <span className="font-bold text-slate-900 font-mono">
                  {totalPages}
                </span>{" "}
                ({totalRecords} records)
              </span>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="gap-1 text-xs"
                >
                  <ChevronLeft className="h-3.5 w-3.5" /> Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="gap-1 text-xs"
                >
                  Next <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
