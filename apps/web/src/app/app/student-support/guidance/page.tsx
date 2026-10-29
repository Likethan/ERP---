"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { StudentSupportService } from "@/services/student-support.service";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  GraduationCap,
  Briefcase,
  BookOpen,
  Calendar,
  Sparkles,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  ExternalLink,
} from "lucide-react";

interface GuidanceEvent {
  id: string;
  date: string;
  sourceModule: "ACADEMIC_ADVISING" | "CAREER_PLACEMENT" | "FACULTY_MENTORING" | "SKILL_WORKSHOP";
  title: string;
  facilitator: string;
  summary: string;
  actionItems?: string[];
  status: "COMPLETED" | "SCHEDULED" | "IN_PROGRESS";
}

const MOCK_GUIDANCE_TIMELINE: GuidanceEvent[] = [
  {
    id: "g-001",
    date: "2026-10-24T14:30:00Z",
    sourceModule: "FACULTY_MENTORING",
    title: "Semester 5 Mid-Term Academic & IDP Review",
    facilitator: "Dr. K. S. Venkatesh (Dept of CSE)",
    summary: "Reviewed distributed systems project milestone, recommended elective options for semester 6, and validated student development progress.",
    actionItems: ["Complete cloud simulator benchmark", "Submit IEEE conference preprint draft"],
    status: "COMPLETED",
  },
  {
    id: "g-002",
    date: "2026-10-18T10:00:00Z",
    sourceModule: "CAREER_PLACEMENT",
    title: "Campus Placement Technical Mock Interview",
    facilitator: "Prof. Ananya Roy (Placement Cell)",
    summary: "Conducted 45-minute live coding simulation and system design assessment. Scored 88/100 on algorithmic logic.",
    actionItems: ["Revise dynamic programming edge cases", "Optimize resume summary block"],
    status: "COMPLETED",
  },
  {
    id: "g-003",
    date: "2026-10-10T16:00:00Z",
    sourceModule: "ACADEMIC_ADVISING",
    title: "Honors Degree & Minor Specialization Advising",
    facilitator: "Dean of Academics Office",
    summary: "Formally approved enrollment in Honors in Artificial Intelligence & Robotics based on cumulative CGPA 8.75.",
    actionItems: ["Enroll in Advanced Robotics Elective 501"],
    status: "COMPLETED",
  },
  {
    id: "g-004",
    date: "2026-11-05T09:30:00Z",
    sourceModule: "SKILL_WORKSHOP",
    title: "Enterprise System Design & Microservices Masterclass",
    facilitator: "Industry Visiting Specialist",
    summary: "Practical laboratory workshop on event-driven architectures, Kafka streams, and distributed transactional consistency.",
    status: "SCHEDULED",
  },
];

export default function AcademicCareerGuidancePage() {
  const [timelineEvents, setTimelineEvents] = useState<GuidanceEvent[]>(MOCK_GUIDANCE_TIMELINE);
  const [filterSource, setFilterSource] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredEvents = timelineEvents.filter((ev) => {
    const matchesSource = filterSource === "ALL" || ev.sourceModule === filterSource;
    const matchesSearch =
      ev.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.facilitator.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.summary.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSource && matchesSearch;
  });

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Guidance Timeline", href: "/app/student-support/guidance" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <GraduationCap className="h-6 w-6 text-indigo-400" />
              Academic & Career Guidance Longitudinal Timeline
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Holistic, privacy-safe record of advising interventions, career readiness sessions, and faculty guidance.
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/app/student-support/sessions">
              <Button className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white">
                <Calendar className="mr-1.5 h-3.5 w-3.5" />
                Schedule Mentoring
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <StudentSupportNav />

      {/* Filter and Search Bar */}
      <Card className="border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search guidance touchpoints, facilitators, or topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-slate-950 border-slate-800 text-xs"
            />
          </div>
          <select
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-300"
          >
            <option value="ALL">All Support Streams</option>
            <option value="FACULTY_MENTORING">Faculty Mentoring</option>
            <option value="CAREER_PLACEMENT">Career & Placement</option>
            <option value="ACADEMIC_ADVISING">Academic Advising</option>
            <option value="SKILL_WORKSHOP">Skill Workshops</option>
          </select>
        </div>
      </Card>

      {/* Timeline Stream */}
      <div className="relative pl-6 border-l-2 border-slate-800 space-y-6">
        {filteredEvents.map((event) => (
          <div key={event.id} className="relative group">
            {/* Timeline dot */}
            <div className="absolute -left-[31px] top-4 h-4 w-4 rounded-full border-2 border-slate-900 bg-indigo-500 group-hover:scale-110 transition-transform" />

            <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-3 hover:border-slate-700 transition">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-sm">{event.title}</span>
                    <Badge
                      variant="outline"
                      className={
                        event.sourceModule === "FACULTY_MENTORING"
                          ? "border-indigo-500/30 text-indigo-400 bg-indigo-500/10 text-[10px]"
                          : event.sourceModule === "CAREER_PLACEMENT"
                          ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-[10px]"
                          : event.sourceModule === "ACADEMIC_ADVISING"
                          ? "border-purple-500/30 text-purple-400 bg-purple-500/10 text-[10px]"
                          : "border-cyan-500/30 text-cyan-400 bg-cyan-500/10 text-[10px]"
                      }
                    >
                      {event.sourceModule.replace("_", " ")}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-400">
                    Facilitator: <span className="text-slate-200">{event.facilitator}</span>
                  </div>
                </div>

                <div className="text-xs text-slate-400">
                  <span className="font-medium text-slate-300">
                    {new Date(event.date).toLocaleDateString()} at{" "}
                    {new Date(event.date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{event.summary}</p>

              {event.actionItems && event.actionItems.length > 0 && (
                <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800 text-xs space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium">Assigned Guidance Actions:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-slate-200">
                    {event.actionItems.map((act, idx) => (
                      <li key={idx}>{act}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          </div>
        ))}
      </div>
    </div>
  );
}
