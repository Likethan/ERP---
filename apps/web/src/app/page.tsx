"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  Server,
  Layers,
  Database,
  CheckCircle2,
  AlertCircle,
  FileCode2,
  Lock,
} from "lucide-react";

interface ApiHealthState {
  status: "checking" | "connected" | "unreachable";
  service?: string;
  version?: string;
}

export default function FoundationPage() {
  const [apiHealth, setApiHealth] = useState<ApiHealthState>({
    status: "checking",
  });

  useEffect(() => {
    async function checkApi() {
      try {
        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/v1/health`, {
          cache: "no-store",
        });
        if (res.ok) {
          const data = await res.json();
          setApiHealth({
            status: "connected",
            service: data.data?.service || "CampusOS API",
            version: data.data?.version || "0.1.0",
          });
        } else {
          setApiHealth({ status: "unreachable" });
        }
      } catch {
        setApiHealth({ status: "unreachable" });
      }
    }
    checkApi();
  }, []);

  const domains = [
    {
      name: "Core",
      desc: "Institutions, Campuses, Departments, Programs, Semesters",
    },
    {
      name: "People",
      desc: "Users, Roles, Permissions, Unified Students, Faculty, Parents",
    },
    { name: "Academics", desc: "Curriculum, Courses, Enrollments, Timetables" },
    { name: "Attendance", desc: "Sessions, Biometrics, Leave Requests" },
    {
      name: "Examination",
      desc: "Assessments, Marks, Grade Scales, GPA Computation",
    },
    {
      name: "Finance",
      desc: "Fee Catalogs, Invoicing, Transactions, Receipts",
    },
    {
      name: "Placement",
      desc: "Corporate Drives, Eligibility Rules, Interviews, Offers",
    },
    { name: "Campus", desc: "Clubs, Events, Broadcasts, Notifications" },
    {
      name: "Infrastructure",
      desc: "Hostel Rooms, Fleet Vehicles, Routes, Stops",
    },
    { name: "Documents", desc: "Certificates, Transcripts, S3 Storage Vault" },
    {
      name: "Intelligence",
      desc: "Analytics Aggregations, Audit Trails, AI Tools",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Top Enterprise Navigation */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-sm tracking-wider">
              COS
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-900">
                  CampusOS
                </span>
                <span className="text-xs px-2 py-0.5 font-medium bg-slate-100 text-slate-700 rounded border border-slate-200">
                  Step 1 • Foundation
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                One Campus. One System. One Source of Truth.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs font-medium px-3 py-1.5 rounded-full border border-slate-200 bg-slate-50">
              <span className="text-slate-500">Backend API:</span>
              {apiHealth.status === "checking" && (
                <span className="flex items-center text-slate-500">
                  <span className="h-2 w-2 rounded-full bg-slate-400 animate-pulse mr-1.5" />
                  Checking...
                </span>
              )}
              {apiHealth.status === "connected" && (
                <span className="flex items-center text-emerald-700 font-semibold">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-1" />
                  Online ({apiHealth.version})
                </span>
              )}
              {apiHealth.status === "unreachable" && (
                <span
                  className="flex items-center text-amber-700"
                  title="Start FastAPI on :8000"
                >
                  <AlertCircle className="h-3.5 w-3.5 text-amber-600 mr-1" />
                  Offline (:8000)
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
        {/* Banner */}
        <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 shadow-sm">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded bg-blue-50 border border-blue-100 text-blue-800 text-xs font-semibold">
              <ShieldCheck className="h-3.5 w-3.5 text-blue-600" />
              <span>Production Architecture Initialized</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Enterprise Campus Operating System
            </h1>
            <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
              The foundational architecture for CampusOS has been established.
              In accordance with engineering standards, no business modules,
              mock data, or fake dashboards have been prematurely introduced.
              Below is the active architectural topology and contract baseline.
            </p>
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-slate-100">
            <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider block">
                Pattern
              </span>
              <span className="text-base font-bold text-slate-900 mt-1 block">
                Modular Monolith
              </span>
            </div>
            <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider block">
                Domains Defined
              </span>
              <span className="text-base font-bold text-slate-900 mt-1 block">
                11 Boundaries
              </span>
            </div>
            <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider block">
                Multi-Tenancy
              </span>
              <span className="text-base font-bold text-slate-900 mt-1 block">
                Row-Level RLS Ready
              </span>
            </div>
            <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider block">
                Authorization
              </span>
              <span className="text-base font-bold text-slate-900 mt-1 block">
                RBAC + PBAC
              </span>
            </div>
          </div>
        </section>

        {/* 4 Foundation Pillars */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1 */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <div className="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-800">
                <Layers className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">
                Frontend & UI Foundation
              </h2>
              <p className="text-sm text-slate-600">
                Next.js 15 App Router configured with strict TypeScript,
                Tailwind CSS, enterprise design tokens, and typed API client
                integration.
              </p>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2">
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>Strict TypeScript & ESLint validation</span>
                </li>
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>Role-specific dashboard routing structure ready</span>
                </li>
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>
                    Shared TypeScript definitions package (@campusos/types)
                  </span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 text-xs text-slate-500 font-mono">
              Directory: apps/web
            </div>
          </div>

          {/* Card 2 */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <div className="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-800">
                <Server className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">
                Backend API Architecture
              </h2>
              <p className="text-sm text-slate-600">
                Python 3.11+ FastAPI backend with asynchronous SQLAlchemy 2.0
                ORM, Pydantic v2 validation, Alembic migrations, and CORS
                protection.
              </p>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2">
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>
                    Standardized ApiResponse and ApiErrorResponse envelopes
                  </span>
                </li>
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>Interactive OpenAPI documentation at /docs</span>
                </li>
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>Automated Pytest suite verifying system health</span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 text-xs text-slate-500 font-mono">
              Directory: apps/api
            </div>
          </div>

          {/* Card 3 */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <div className="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-800">
                <Database className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">
                Database & Multi-Tenancy Model
              </h2>
              <p className="text-sm text-slate-600">
                PostgreSQL 16 base with UUIDv4 primary keys, UTC timestamp
                tracking, and row-level tenant isolation via mandatory tenant_id
                references.
              </p>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2">
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>
                    Single Source of Truth: Student is never duplicated
                  </span>
                </li>
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>
                    PostgreSQL Row-Level Security (RLS) policy blueprint
                  </span>
                </li>
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>
                    Immutable audit logging for critical administrative events
                  </span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 text-xs text-slate-500 font-mono">
              Strategy: Row-Level Isolation (TenantScopedModel)
            </div>
          </div>

          {/* Card 4 */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <div className="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-800">
                <Lock className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">
                Security & Zero-Trust Boundary
              </h2>
              <p className="text-sm text-slate-600">
                Argon2id password hashing, stateless JWT with secure HttpOnly
                cookies, and atomic permission checks enforced strictly at API
                route guards.
              </p>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2">
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>Permissions never trusted from frontend state</span>
                </li>
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>
                    Role-based + Permission-based authorization (RBAC/PBAC)
                  </span>
                </li>
                <li className="flex items-center text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-2 flex-shrink-0" />
                  <span>
                    AI execution strictly bounded by permission-checked tools
                  </span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 text-xs text-slate-500 font-mono">
              Pattern: Zero-Trust Gateway Guard
            </div>
          </div>
        </section>

        {/* Domain Catalog */}
        <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Registered Domain Boundaries
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                11 discrete business domains organized under
                apps/api/app/domains/
              </p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-md border border-slate-200">
              11 Modules
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {domains.map((d, index) => (
              <div
                key={d.name}
                className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-white hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-slate-400">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="font-semibold text-sm text-slate-900">
                    {d.name}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1.5 leading-snug">
                  {d.desc}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Documentation Index */}
        <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 shadow-sm">
          <div className="flex items-center space-x-2 text-slate-900 mb-4">
            <FileCode2 className="h-5 w-5 text-slate-700" />
            <h2 className="text-lg font-bold">
              Architecture Documentation Suite
            </h2>
          </div>
          <p className="text-sm text-slate-600 mb-6">
            Complete technical specifications and Architecture Decision Records
            (ADRs) are available in the{" "}
            <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs font-mono">
              /docs
            </code>{" "}
            directory.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
              <span className="font-bold text-slate-800 block">Product</span>
              <span className="text-slate-500 mt-1 block">
                docs/product/overview.md
              </span>
              <span className="text-slate-500 block">
                docs/product/roadmap.md
              </span>
            </div>
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
              <span className="font-bold text-slate-800 block">
                Architecture
              </span>
              <span className="text-slate-500 mt-1 block">
                docs/architecture/system-overview.md
              </span>
              <span className="text-slate-500 block">
                docs/architecture/domain-boundaries.md
              </span>
            </div>
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
              <span className="font-bold text-slate-800 block">
                Security & API
              </span>
              <span className="text-slate-500 mt-1 block">
                docs/security/architecture.md
              </span>
              <span className="text-slate-500 block">
                docs/api/standards.md
              </span>
            </div>
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
              <span className="font-bold text-slate-800 block">
                Decisions (ADRs)
              </span>
              <span className="text-slate-500 mt-1 block">
                ADR-001: Modular Monolith
              </span>
              <span className="text-slate-500 block">
                ADR-002: Multi-Tenancy RLS
              </span>
              <span className="text-slate-500 block">ADR-003: RBAC + PBAC</span>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500">
          CampusOS Platform Foundation • Step 1 Complete • Strictly Isolated
          Architecture
        </div>
      </footer>
    </div>
  );
}
