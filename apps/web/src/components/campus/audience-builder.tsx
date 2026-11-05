"use client";

import React, { useState } from "react";
import { EventAudienceTarget, EventAudienceType } from "@/types/campus";
import { calculateAudienceSize } from "@/services/campus-calculator";
import { Users, Filter, CheckCircle2, Info } from "lucide-react";

interface AudienceBuilderProps {
  value: EventAudienceTarget;
  onChange: (target: EventAudienceTarget) => void;
  disabled?: boolean;
}

const AUDIENCE_TYPES: {
  id: EventAudienceType;
  label: string;
  description: string;
}[] = [
  {
    id: "ALL_STUDENTS",
    label: "All Enrolled Students",
    description: "All undergraduate & postgraduate student cohorts",
  },
  {
    id: "SPECIFIC_DEPARTMENT",
    label: "Specific Department",
    description: "Target a specific department (e.g. Computer Science)",
  },
  {
    id: "SPECIFIC_PROGRAM",
    label: "Specific Degree Program",
    description: "Target a degree program (e.g. B.Tech Computer Science)",
  },
  {
    id: "SPECIFIC_SEMESTER",
    label: "Specific Semester",
    description: "Target students by academic semester cohort",
  },
  {
    id: "FACULTY",
    label: "All Faculty Members",
    description: "Full-time, visiting, and research faculty",
  },
  {
    id: "STAFF",
    label: "University Staff",
    description: "Technical, laboratory, and administrative staff",
  },
  {
    id: "CLUB_MEMBERS",
    label: "Club Members",
    description: "Members belonging to an active student organization",
  },
  {
    id: "CUSTOM",
    label: "Custom Filtered Audience",
    description: "Custom query combining department, semester, and eligibility",
  },
];

const DEPARTMENTS = [
  "Computer Science & Engineering",
  "Artificial Intelligence & Data Science",
  "Electronics & Communication Engineering",
  "Mechanical Engineering",
  "Civil Engineering",
  "Electrical & Electronics Engineering",
];

const PROGRAMS = [
  "B.Tech Computer Science & Engineering",
  "B.Tech Artificial Intelligence & Data Science",
  "B.Tech Electronics & Communication",
  "B.Tech Mechanical Engineering",
  "M.Tech Software Engineering",
];

const CLUBS = [
  "Association of Computer Engineers (ACE)",
  "Autonomous Robotics & Embedded Systems Club",
  "Dhwani Cultural & Fine Arts Guild",
  "Innovation & Entrepreneurship Cell",
  "Apex Sports & Athletics Guild",
  "Odyssey Literary & Debating Society",
];

export function AudienceBuilder({
  value,
  onChange,
  disabled,
}: AudienceBuilderProps) {
  const [targetType, setTargetType] = useState<EventAudienceType>(
    value.type || "ALL_STUDENTS",
  );
  const [selectedDept, setSelectedDept] = useState(
    value.departmentName || DEPARTMENTS[0],
  );
  const [selectedProgram, setSelectedProgram] = useState(
    value.programName || PROGRAMS[0],
  );
  const [selectedSemester, setSelectedSemester] = useState(value.semester || 5);
  const [selectedClub, setSelectedClub] = useState(value.clubName || CLUBS[0]);
  const [customDescription, setCustomDescription] = useState(
    value.customDescription || "",
  );

  const emitChange = (updates: Partial<EventAudienceTarget>) => {
    const updatedTarget: EventAudienceTarget = {
      ...value,
      type: targetType,
      departmentName: selectedDept,
      programName: selectedProgram,
      semester: selectedSemester,
      clubName: selectedClub,
      customDescription,
      ...updates,
    };
    const estimatedCount = calculateAudienceSize({
      type: updatedTarget.type,
      departmentName: updatedTarget.departmentName,
      programName: updatedTarget.programName,
      semester: updatedTarget.semester,
    });
    updatedTarget.estimatedCount = estimatedCount;
    onChange(updatedTarget);
  };

  const handleTypeSelect = (type: EventAudienceType) => {
    setTargetType(type);
    emitChange({ type });
  };

  const estimated = calculateAudienceSize({
    type: targetType,
    departmentName: selectedDept,
    programName: selectedProgram,
    semester: selectedSemester,
  });

  return (
    <div className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      {/* Header with Live Audience Estimation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <Filter className="h-4 w-4 text-yellow-600" />
            Audience Targeting Matrix
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure participant eligibility criteria and recipient scope
          </p>
        </div>
        <div className="flex items-center gap-2 bg-yellow-50 border border-yellow-200 px-3.5 py-1.5 rounded-xl self-start sm:self-auto">
          <Users className="h-4 w-4 text-yellow-600" />
          <div className="text-xs">
            <span className="text-slate-600">Estimated Reach: </span>
            <span className="font-bold text-slate-950 font-mono">
              {estimated.toLocaleString()} users
            </span>
          </div>
        </div>
      </div>

      {/* Target Type Selector Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {AUDIENCE_TYPES.map((t) => {
          const isSelected = targetType === t.id;
          return (
            <button
              key={t.id}
              type="button"
              disabled={disabled}
              onClick={() => handleTypeSelect(t.id)}
              className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                isSelected
                  ? "bg-yellow-50 border-yellow-400 text-slate-950 shadow-xs ring-1 ring-yellow-400/50"
                  : "bg-slate-50/70 border-slate-200 text-slate-700 hover:border-yellow-300 hover:bg-yellow-50/20 hover:text-slate-900"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold">{t.label}</span>
                {isSelected && (
                  <CheckCircle2 className="h-3.5 w-3.5 text-yellow-600 shrink-0" />
                )}
              </div>
              <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-tight">
                {t.description}
              </p>
            </button>
          );
        })}
      </div>

      {/* Conditional Parameters */}
      {targetType === "SPECIFIC_DEPARTMENT" && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <label className="text-xs font-semibold text-slate-700">
            Target Department
          </label>
          <select
            value={selectedDept}
            disabled={disabled}
            onChange={(e) => {
              setSelectedDept(e.target.value);
              emitChange({ departmentName: e.target.value });
            }}
            className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 shadow-2xs"
          >
            {DEPARTMENTS.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
        </div>
      )}

      {targetType === "SPECIFIC_PROGRAM" && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <label className="text-xs font-semibold text-slate-700">
            Target Degree Program
          </label>
          <select
            value={selectedProgram}
            disabled={disabled}
            onChange={(e) => {
              setSelectedProgram(e.target.value);
              emitChange({ programName: e.target.value });
            }}
            className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 shadow-2xs"
          >
            {PROGRAMS.map((prog) => (
              <option key={prog} value={prog}>
                {prog}
              </option>
            ))}
          </select>
        </div>
      )}

      {targetType === "SPECIFIC_SEMESTER" && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Department
              </label>
              <select
                value={selectedDept}
                disabled={disabled}
                onChange={(e) => {
                  setSelectedDept(e.target.value);
                  emitChange({ departmentName: e.target.value });
                }}
                className="mt-1 w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 shadow-2xs"
              >
                {DEPARTMENTS.map((dept) => (
                  <option key={dept} value={dept}>
                    {dept}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Semester
              </label>
              <select
                value={selectedSemester}
                disabled={disabled}
                onChange={(e) => {
                  const sem = parseInt(e.target.value, 10);
                  setSelectedSemester(sem);
                  emitChange({ semester: sem });
                }}
                className="mt-1 w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 shadow-2xs"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s} (Year {Math.ceil(s / 2)})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {targetType === "CLUB_MEMBERS" && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <label className="text-xs font-semibold text-slate-700">
            Selecting Club or Organization
          </label>
          <select
            value={selectedClub}
            disabled={disabled}
            onChange={(e) => {
              setSelectedClub(e.target.value);
              emitChange({ clubName: e.target.value });
            }}
            className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 shadow-2xs"
          >
            {CLUBS.map((club) => (
              <option key={club} value={club}>
                {club}
              </option>
            ))}
          </select>
        </div>
      )}

      {targetType === "CUSTOM" && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <label className="text-xs font-semibold text-slate-700">
            Audience Targeting Specifications
          </label>
          <input
            type="text"
            disabled={disabled}
            value={customDescription}
            onChange={(e) => {
              setCustomDescription(e.target.value);
              emitChange({ customDescription: e.target.value });
            }}
            placeholder="e.g. Department = AI & DS AND Semester = 7 AND CGPA >= 7.50"
            className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 shadow-2xs"
          />
        </div>
      )}

      <div className="flex items-center gap-2 text-[11px] text-slate-600 bg-yellow-50/50 p-2.5 rounded-lg border border-yellow-200/60">
        <Info className="h-3.5 w-3.5 text-yellow-600 shrink-0" />
        <span>
          Audience calculations are synchronized against live campus student
          enrollments.
        </span>
      </div>
    </div>
  );
}
