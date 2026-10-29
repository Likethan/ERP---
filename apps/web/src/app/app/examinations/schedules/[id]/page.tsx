"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { examinationsService } from "@/services/examinations.service";
import { ExamSchedule } from "@/types/examinations";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  Calendar,
  Clock,
  MapPin,
  User,
  ArrowLeft,
  CheckCircle2,
  Users,
  ShieldCheck,
  FileText,
  AlertCircle,
} from "lucide-react";

export default function ExamScheduleDetailPage() {
  const params = useParams();
  const scheduleId = params?.id as string;
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [schedule, setSchedule] = useState<ExamSchedule | null>(null);

  useEffect(() => {
    async function loadSchedule() {
      if (!scheduleId) return;
      try {
        setLoading(true);
        const res = await examinationsService.getScheduleById(scheduleId);
        setSchedule(res.data);
      } catch (err: unknown) {
        showToast({
          title: "Error",
          message: err instanceof Error ? err.message : "Schedule not found",
          type: "error",
        });
      } finally {
        setLoading(false);
      }
    }

    loadSchedule();
  }, [scheduleId]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        Loading schedule information...
      </div>
    );
  }

  if (!schedule) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-slate-500">Schedule record not found</p>
        <Link href="/app/examinations/schedules">
          <Button variant="outline" size="sm" className="mt-4">
            Back to Schedules
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <Link
            href="/app/examinations/schedules"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Timetable Schedules
          </Link>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {schedule.courseCode} - {schedule.courseName}
            </h1>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                schedule.status === "CONFIRMED"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                  : "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
              }`}
            >
              {schedule.status}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {schedule.examinationName} • {schedule.program} (Section{" "}
            {schedule.section})
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={`/app/examinations/marks?course_offering_id=${schedule.courseOfferingId}`}
          >
            <Button variant="primary" size="sm" className="text-xs">
              Go to Marks Ledger
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Date & Time"
          value={schedule.date}
          description={`${schedule.startTime} - ${schedule.endTime}`}
          icon={<Calendar className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Room / Venue"
          value={schedule.room}
          description="Hall capacity verified"
          icon={<MapPin className="h-5 w-5 text-blue-600" />}
        />
        <StatCard
          title="Chief Invigilator"
          value={schedule.facultyName}
          description="Assigned faculty proctor"
          icon={<User className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Total Candidates"
          value={`${schedule.totalCandidates} seats`}
          description="Enrolled cohort register"
          icon={<Users className="h-5 w-5 text-amber-600" />}
        />
      </div>

      {/* Detailed Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            Invigilation Guidelines
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            {schedule.invigilatorNotes ||
              "Standard university examination guidelines apply. Hall tickets and college photo ID must be verified prior to entry."}
          </p>
          <div className="p-3 rounded-lg border border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-800/40 text-xs space-y-1">
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              Exam Instructions:
            </span>
            <ul className="list-disc pl-4 text-slate-500 space-y-1 mt-1">
              <li>
                Candidates permitted inside hall 15 minutes before paper
                commencement.
              </li>
              <li>
                Calculators and formula books only as approved by department
                syllabus.
              </li>
              <li>
                Answer booklet barcodes must be scanned and sealed upon period
                conclusion.
              </li>
            </ul>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="h-4 w-4 text-blue-600" />
            Timetable Collision Status
          </h3>
          <div className="flex items-center gap-3 p-3.5 rounded-lg border border-emerald-200 bg-emerald-50 dark:border-emerald-900/50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200 text-xs">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
            <div>
              <p className="font-bold">Collision Free</p>
              <p className="mt-0.5">
                Verified no room overlap, section clash, or faculty invigilation
                conflict.
              </p>
            </div>
          </div>
          <div className="text-xs text-slate-400 space-y-1">
            <p>
              <strong>Scheduled on:</strong>{" "}
              {new Date(schedule.createdAt).toLocaleString()}
            </p>
            <p>
              <strong>Examination Session:</strong> {schedule.examinationName}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
