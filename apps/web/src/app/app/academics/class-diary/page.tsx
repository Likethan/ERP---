"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { teachingService } from "@/services/teaching.service";
import { ClassDiaryEntry, TeachingMethod } from "@/types/teaching";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  Calendar,
  Plus,
  BookOpen,
  CheckCircle2,
  Clock,
  Layers,
  ArrowRight,
  TrendingUp,
  FileCheck2,
  Users,
  Award,
  Sparkles,
} from "lucide-react";

export default function ClassDiaryPage() {
  const { user, activePersona } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [entries, setEntries] = useState<ClassDiaryEntry[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("co-cs301-a");

  // Create Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    courseOfferingId: "co-cs301-a",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "A",
    date: new Date().toISOString().split("T")[0],
    timeSlot: "09:00 AM - 10:00 AM",
    periodNumber: 1,
    unitNumber: 3,
    unitTitle: "Graph Algorithms & Network Flows",
    topicsCovered: "",
    teachingMethod: "CHALK_AND_BOARD" as TeachingMethod,
    studentsPresent: 46,
    totalStudents: 48,
    remarks: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await teachingService.getClassDiaryEntries(selectedCourse);
      if (res.success) {
        setEntries(res.data);
      }
    } catch (err) {
      console.error(err);
      showToast({
        type: "error",
        title: "Error",
        message: "Failed to load class diary.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCourse]);

  const totalSessionsLogged = entries.length;
  const avgAttendance = useMemo(() => {
    if (entries.length === 0) return 0;
    const sum = entries.reduce(
      (acc, curr) => acc + curr.attendancePercentage,
      0,
    );
    return Math.round((sum / entries.length) * 10) / 10;
  }, [entries]);

  const handleLogEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.topicsCovered.trim()) {
      showToast({
        type: "error",
        title: "Validation Error",
        message: "Topics Covered is required.",
      });
      return;
    }
    try {
      setSubmitting(true);
      const res = await teachingService.logClassDiaryEntry({
        courseOfferingId: formData.courseOfferingId,
        courseCode: formData.courseCode,
        courseName: formData.courseName,
        section: formData.section,
        facultyId: activePersona?.id || "fac-cse-01",
        facultyName: activePersona?.name || "Dr. Rajesh Sharma",
        date: formData.date,
        timeSlot: formData.timeSlot,
        periodNumber: Number(formData.periodNumber),
        unitNumber: Number(formData.unitNumber),
        unitTitle: formData.unitTitle,
        topicsCovered: formData.topicsCovered,
        teachingMethod: formData.teachingMethod,
        studentsPresent: Number(formData.studentsPresent),
        totalStudents: Number(formData.totalStudents),
        attendancePercentage: 0,
        remarks: formData.remarks,
        verifiedByHod: true,
      });

      if (res.success) {
        showToast({
          type: "success",
          title: "Session Logged",
          message:
            "Class diary entry recorded and syllabus unit completion updated.",
        });
        setCreateModalOpen(false);
        setFormData({ ...formData, topicsCovered: "", remarks: "" });
        await loadData();
      }
    } catch (err: any) {
      showToast({
        type: "error",
        title: "Logging Failed",
        message: err.message,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs border-l-4 border-l-yellow-400">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-semibold text-yellow-950 border border-yellow-300 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-600" />
            Classroom Teaching Log & Pedagogy Ledger
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Class Diary / Teaching Log
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Daily lecture session logbook tracking topics taught, pedagogy
            methods, attendance count, and HOD verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/academics/lesson-plans">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Layers className="h-3.5 w-3.5" />}
            >
              Lesson Plans
            </Button>
          </Link>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-3.5 w-3.5" />}
            onClick={() => setCreateModalOpen(true)}
          >
            Log Lecture Session
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Total Sessions Logged"
          value={totalSessionsLogged}
          description="Audited lecture entries in diary"
          variant="indigo"
          icon={<BookOpen className="h-4 w-4" />}
        />
        <StatCard
          label="Average Class Attendance"
          value={`${avgAttendance}%`}
          description="Average student turnout in sessions"
          variant="emerald"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="HOD Endorsement Rate"
          value="100%"
          description="All diary entries signed by HOD"
          variant="amber"
          icon={<FileCheck2 className="h-4 w-4" />}
        />
      </div>

      {/* Course Filter */}
      <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-3">
          <BookOpen className="h-4 w-4 text-yellow-600" />
          <span className="text-xs font-semibold text-slate-800">
            Assigned Course Offering:
          </span>
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
          >
            <option value="co-cs301-a">
              CS301 — Data Structures & Algorithms (Sec A)
            </option>
            <option value="co-cs501-a">CS501 — Compiler Design (Sec A)</option>
            <option value="co-cs402-b">
              CS402 — Operating Systems (Sec B)
            </option>
          </select>
        </div>

        <div className="text-xs text-slate-500">
          Faculty:{" "}
          <strong className="text-slate-800">
            {activePersona?.name || "Dr. Rajesh Sharma"}
          </strong>
        </div>
      </div>

      {/* Diary Entries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recorded Teaching Log Entries</CardTitle>
          <CardDescription>
            Chronological audit of lecture hours delivered with pedagogy records
            and student attendance counts.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-600">
                  <th className="py-3 px-4">Date & Slot</th>
                  <th className="py-3 px-4">Period / Unit</th>
                  <th className="py-3 px-4">Topics Covered</th>
                  <th className="py-3 px-4">Pedagogy Method</th>
                  <th className="py-3 px-4">Turnout</th>
                  <th className="py-3 px-4 text-right">Verification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      Loading diary entries...
                    </td>
                  </tr>
                ) : entries.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No diary entries logged for this course yet.
                    </td>
                  </tr>
                ) : (
                  entries.map((entry) => (
                    <tr
                      key={entry.id}
                      className="hover:bg-yellow-50/20 transition-colors"
                    >
                      <td className="py-3.5 px-4 font-mono font-medium text-slate-900">
                        {entry.date}
                        <div className="text-[11px] text-slate-500 font-sans">
                          {entry.timeSlot}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-semibold text-slate-800">
                          Period {entry.periodNumber}
                        </span>
                        <div className="text-[11px] text-slate-500">
                          Unit {entry.unitNumber}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 max-w-md">
                        <div className="font-medium text-slate-900">
                          {entry.topicsCovered}
                        </div>
                        {entry.remarks && (
                          <div className="text-[11px] text-slate-500 mt-0.5 italic">
                            "{entry.remarks}"
                          </div>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <Badge
                          variant="outline"
                          className="text-[10px] font-mono"
                        >
                          {entry.teachingMethod.replace(/_/g, " ")}
                        </Badge>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900">
                          {entry.studentsPresent} / {entry.totalStudents}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          {entry.attendancePercentage}% Present
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <Badge
                          variant={entry.verifiedByHod ? "success" : "warning"}
                          dot
                        >
                          {entry.verifiedByHod ? "HOD Signed" : "Pending Sign"}
                        </Badge>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Log Session Dialog */}
      <Dialog
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Log Classroom Lecture Session"
      >
        <form onSubmit={handleLogEntry} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Lecture Date
              </label>
              <Input
                type="date"
                value={formData.date}
                onChange={(e) =>
                  setFormData({ ...formData, date: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Period Number
              </label>
              <Input
                type="number"
                min="1"
                max="8"
                value={formData.periodNumber}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    periodNumber: Number(e.target.value),
                  })
                }
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Time Slot
              </label>
              <select
                value={formData.timeSlot}
                onChange={(e) =>
                  setFormData({ ...formData, timeSlot: e.target.value })
                }
                className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              >
                <option value="09:00 AM - 10:00 AM">
                  09:00 AM - 10:00 AM (P1)
                </option>
                <option value="10:00 AM - 11:00 AM">
                  10:00 AM - 11:00 AM (P2)
                </option>
                <option value="11:15 AM - 12:15 PM">
                  11:15 AM - 12:15 PM (P3)
                </option>
                <option value="01:00 PM - 02:00 PM">
                  01:00 PM - 02:00 PM (P4)
                </option>
                <option value="02:00 PM - 03:00 PM">
                  02:00 PM - 03:00 PM (P5)
                </option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Syllabus Unit
              </label>
              <select
                value={formData.unitNumber}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    unitNumber: Number(e.target.value),
                  })
                }
                className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              >
                <option value="1">Unit 1: Linear Structures</option>
                <option value="2">Unit 2: Balanced Trees</option>
                <option value="3">Unit 3: Graph Algorithms</option>
                <option value="4">Unit 4: Hashing & Heaps</option>
                <option value="5">Unit 5: NP-Completeness</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Topics Covered in Class
            </label>
            <textarea
              rows={3}
              placeholder="Detail the exact concepts, algorithms, and proofs taught during this lecture..."
              className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              value={formData.topicsCovered}
              onChange={(e) =>
                setFormData({ ...formData, topicsCovered: e.target.value })
              }
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Pedagogy / Teaching Method
              </label>
              <select
                value={formData.teachingMethod}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    teachingMethod: e.target.value as TeachingMethod,
                  })
                }
                className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              >
                <option value="CHALK_AND_BOARD">Chalk & Board</option>
                <option value="POWERPOINT_ICT">PowerPoint ICT Slides</option>
                <option value="LAB_DEMONSTRATION">
                  Live Code Demonstration
                </option>
                <option value="PROBLEM_SOLVING">
                  Tutorial Problem Solving
                </option>
                <option value="GROUP_DISCUSSION">
                  Active Group Discussion
                </option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Students Present
              </label>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  min="0"
                  max="60"
                  value={formData.studentsPresent}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      studentsPresent: Number(e.target.value),
                    })
                  }
                  required
                />
                <span className="text-xs text-slate-500 whitespace-nowrap">
                  / {formData.totalStudents}
                </span>
              </div>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Observations & Student Engagement Remarks
            </label>
            <Input
              placeholder="e.g. Students completed AVL rotation exercise on whiteboard."
              value={formData.remarks}
              onChange={(e) =>
                setFormData({ ...formData, remarks: e.target.value })
              }
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button
              variant="ghost"
              size="sm"
              type="button"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Recording..." : "Save to Class Diary"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
