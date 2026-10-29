"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Sparkles,
  ArrowLeft,
  ArrowRight,
  User,
  Calendar,
  GraduationCap,
  IndianRupee,
  Briefcase,
  FileCheck,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  ExternalLink,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { intelligenceService } from "@/services/intelligence.service";
import { StudentIntelligenceProfile } from "@campusos/types";

export default function StudentIntelligence360Page() {
  const params = useParams();
  const studentId = params?.id as string;

  const [profile, setProfile] = useState<StudentIntelligenceProfile | null>(
    null,
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        const res =
          await intelligenceService.getStudentIntelligenceProfile(studentId);
        if (res.success && res.data) {
          setProfile(res.data);
        }
      } finally {
        setLoading(false);
      }
    };
    if (studentId) fetchProfile();
  }, [studentId]);

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200 space-y-4">
        <p className="text-sm text-slate-500">
          Student intelligence profile not found for ID {studentId}.
        </p>
        <Link href="/app/students">
          <Button size="sm" variant="outline">
            Return to Students Roster
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Breadcrumbs
            items={[
              { label: "Dashboard", href: "/app/dashboard" },
              { label: "Intelligence", href: "/app/intelligence" },
              { label: "Students", href: "/app/students" },
              { label: `${profile.studentName} Intelligence 360` },
            ]}
          />
          <div className="flex items-center gap-2 mt-1">
            <Link href={`/app/students/${profile.studentId}`}>
              <Button
                variant="ghost"
                size="sm"
                className="p-1 h-7 w-7 text-slate-500"
              >
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
              {profile.studentName} — Intelligence Dossier
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {profile.rollNumber} • {profile.program} • Semester{" "}
            {profile.semester}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href={`/app/students/${profile.studentId}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <User className="w-3.5 h-3.5" />
              Core Student Profile
            </Button>
          </Link>
          <Link
            href={`/app/intelligence/assistant?q=Summarize%20attendance%20and%20academic%20standing%20for%20${profile.studentName}`}
          >
            <Button
              size="sm"
              className="gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Ask AI about Student
            </Button>
          </Link>
        </div>
      </div>

      {/* 6 Core Intelligence Vectors (Section 33) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Attendance Risk */}
        <div className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 block truncate">
            Attendance Risk
          </span>
          <Badge
            variant={
              profile.attendanceRisk === "LOW"
                ? "success"
                : profile.attendanceRisk === "MEDIUM"
                  ? "warning"
                  : "danger"
            }
            className="text-xs font-bold"
          >
            {profile.attendanceRisk}
          </Badge>
          <p className="text-xs font-semibold text-slate-900 pt-1">
            {profile.attendancePercentage}%
          </p>
        </div>

        {/* Academic Trend */}
        <div className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 block truncate">
            Academic Trend
          </span>
          <Badge variant="info" className="text-xs font-semibold">
            {profile.academicTrend}
          </Badge>
          <p className="text-xs font-semibold text-slate-900 pt-1">
            CGPA {profile.cgpa}
          </p>
        </div>

        {/* Finance Status */}
        <div className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 block truncate">
            Finance Status
          </span>
          <Badge
            variant={profile.financeStatus === "CLEAR" ? "success" : "danger"}
            className="text-xs font-bold"
          >
            {profile.financeStatus}
          </Badge>
          <p className="text-xs font-semibold text-slate-900 pt-1">
            {profile.outstandingBalance > 0
              ? `₹${profile.outstandingBalance.toLocaleString()}`
              : "Dues Clear"}
          </p>
        </div>

        {/* Placement Readiness */}
        <div className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 block truncate">
            Placement Status
          </span>
          <Badge variant="neutral" className="text-xs font-semibold">
            {profile.placementReadiness}
          </Badge>
          <p className="text-xs text-slate-500 pt-1">Tier-1 Eligible</p>
        </div>

        {/* Document Completion */}
        <div className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 block truncate">
            Records Compliant
          </span>
          <Badge variant="success" className="text-xs font-bold">
            {profile.documentCompletionRate}%
          </Badge>
          <p className="text-xs text-slate-500 pt-1">
            {profile.missingDocumentsCount} Missing
          </p>
        </div>

        {/* Campus Engagement */}
        <div className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 block truncate">
            Engagement
          </span>
          <Badge variant="info" className="text-xs font-semibold">
            {profile.campusEngagement}
          </Badge>
          <p className="text-xs text-slate-500 pt-1">
            {profile.clubMemberships} Clubs • {profile.eventParticipations}{" "}
            Fests
          </p>
        </div>
      </div>

      {/* Recommended Operational Interventions */}
      <Card>
        <CardHeader className="py-3 px-4 border-b border-slate-100">
          <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-blue-600" />
            Suggested Academic Advisor & Departmental Interventions
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <ul className="space-y-2.5 text-xs text-slate-700">
            {profile.recommendedActions.map((act, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-50 border border-slate-200"
              >
                <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed font-medium">{act}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
