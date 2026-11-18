"use client";

import React, { useState, useEffect, Suspense } from "react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Eye,
  EyeOff,
  AlertCircle,
  ShieldCheck,
  GraduationCap,
  Users,
  Landmark,
  Building,
} from "lucide-react";
import {
  PORTALS,
  ALL_PORTAL_KEYS,
  getRoleIcon,
  type PortalKey,
  type PrimaryPortalKey,
} from "@/lib/portals";
import { getNormalizedRoleSet } from "@/components/navigation/portal-nav";
import { cn } from "@/lib/utils";

interface RoleMeta {
  key: PortalKey;
  label: string;
  tabLabel: string;
  portalTitle: string;
  quote: string;
  badgeIcon: string;
  badgeLabel: string;
  identifierLabel: string;
  identifierPlaceholder: string;
  identifierHint: string;
  ctaText: string;
  persona: {
    name: string;
    roleTitle: string;
    avatarInitials: string;
    demoEmail: string;
    demoPassword: string;
  };
}

const ROLE_METAS: Record<PrimaryPortalKey, RoleMeta> = {
  STUDENT: {
    key: "STUDENT",
    label: "Student",
    tabLabel: "Student",
    portalTitle: "Student Portal",
    quote: "Access your academic life in one place.",
    badgeIcon: "🎓",
    badgeLabel: "Academic Lifecycle & Courses",
    identifierLabel: "STUDENT ID / ROLL NO. OR EMAIL",
    identifierPlaceholder:
      "e.g. aarav.patel@student.campusos.edu or 2024-CSE-042",
    identifierHint: "Use your university roll number or student email.",
    ctaText: "Sign In to Student Portal →",
    persona: {
      name: "Aarav Patel",
      roleTitle: "Student — B.Tech CSE (Year 3 / Sem 5)",
      avatarInitials: "AP",
      demoEmail: "aarav.patel@student.campusos.edu",
      demoPassword: "Password@123",
    },
  },
  FACULTY: {
    key: "FACULTY",
    label: "Faculty",
    tabLabel: "Faculty",
    portalTitle: "Faculty Portal",
    quote: "Teaching, attendance, internal assessments and student mentoring.",
    badgeIcon: "👨‍🏫",
    badgeLabel: "Teaching & Attendance",
    identifierLabel: "FACULTY ID OR EMAIL",
    identifierPlaceholder: "e.g. rajesh.sharma@campusos.edu or FAC-CSE-012",
    identifierHint: "Use your faculty employee ID or institutional email.",
    ctaText: "Sign In to Faculty Portal →",
    persona: {
      name: "Dr. Rajesh Sharma",
      roleTitle: "Professor of Systems & Dean Academics",
      avatarInitials: "RS",
      demoEmail: "rajesh.sharma@campusos.edu",
      demoPassword: "Password@123",
    },
  },
  VICE_PRINCIPAL: {
    key: "VICE_PRINCIPAL",
    label: "Vice Principal",
    tabLabel: "Vice Principal",
    portalTitle: "Vice Principal Portal",
    quote: "Institutional oversight, academic performance, and governance.",
    badgeIcon: "🏛️",
    badgeLabel: "Academic Oversight & Operations",
    identifierLabel: "INSTITUTIONAL EMAIL OR VP ID",
    identifierPlaceholder: "e.g. vp.academics@campusos.edu",
    identifierHint: "Use your institutional executive credentials.",
    ctaText: "Sign In to Vice Principal Portal →",
    persona: {
      name: "Dr. Arvind Swaminathan",
      roleTitle: "Vice Principal (Academic & Operations)",
      avatarInitials: "AS",
      demoEmail: "vp.academics@campusos.edu",
      demoPassword: "Password@123",
    },
  },
  HOD: {
    key: "HOD",
    label: "Head of Department",
    tabLabel: "HOD",
    portalTitle: "HOD Portal",
    quote:
      "Department administration, course allocation, and academic coordination.",
    badgeIcon: "🏢",
    badgeLabel: "Departmental Administration",
    identifierLabel: "HOD ID OR DEPARTMENTAL EMAIL",
    identifierPlaceholder: "e.g. hod.cse@campusos.edu",
    identifierHint: "Use your departmental leadership credentials.",
    ctaText: "Sign In to HOD Portal →",
    persona: {
      name: "Dr. K. S. Anand",
      roleTitle: "Head of Department — Computer Science & Engineering",
      avatarInitials: "KA",
      demoEmail: "hod.cse@campusos.edu",
      demoPassword: "Password@123",
    },
  },
  ADMIN: {
    key: "ADMIN",
    label: "Administrator",
    tabLabel: "Admin",
    portalTitle: "Admin Portal",
    quote:
      "Complete institutional governance, audit logs, and security controls.",
    badgeIcon: "🛡️",
    badgeLabel: "Institutional Administration",
    identifierLabel: "ADMINISTRATOR USERNAME OR EMAIL",
    identifierPlaceholder: "e.g. registrar@campusos.edu",
    identifierHint: "Use your institutional administrator credentials.",
    ctaText: "Sign In to Admin Portal →",
    persona: {
      name: "Registrar Swaminathan",
      roleTitle: "System & Campus Super Administrator",
      avatarInitials: "SA",
      demoEmail: "registrar@campusos.edu",
      demoPassword: "Password@123",
    },
  },
};

const FOUR_ROLES: PrimaryPortalKey[] = [
  "STUDENT",
  "FACULTY",
  "VICE_PRINCIPAL",
  "HOD",
];

function resolvePortalKey(
  rawRole: string | null | undefined,
): PortalKey | null {
  if (!rawRole) return null;
  const r = rawRole.toLowerCase().trim();
  if (r === "student") return "STUDENT";
  if (r === "faculty" || r === "professor") return "FACULTY";
  if (r === "hod") return "HOD";
  if (
    r === "vice-principal" ||
    r === "vice_principal" ||
    r === "principal" ||
    r === "vp"
  )
    return "VICE_PRINCIPAL";
  if (r === "admin" || r === "super_admin" || r === "super-admin")
    return "ADMIN";
  if (r === "accounts" || r === "finance" || r === "bursar") return "ACCOUNTS";
  if (r === "placement" || r === "placement_officer" || r === "tpo")
    return "PLACEMENT";
  if (r === "warden" || r === "hostel") return "WARDEN";
  if (r === "transport" || r === "transport_officer" || r === "fleet")
    return "TRANSPORT";
  if (r === "library" || r === "librarian") return "LIBRARIAN";
  if (r === "security" || r === "security_officer" || r === "security_head")
    return "SECURITY";
  if (r === "facility" || r === "facilities" || r === "estate")
    return "FACILITY";
  if (r === "staff") return "STAFF";
  return null;
}

function LoginFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoading, login, clearSession } = useAuth();

  const [activeRole, setActiveRole] = useState<PortalKey>(() => {
    const fromParam = resolvePortalKey(searchParams.get("role"));
    return fromParam || "STUDENT";
  });

  useEffect(() => {
    const fromUrl = resolvePortalKey(searchParams.get("role"));
    if (fromUrl) {
      setActiveRole(fromUrl);
    }
  }, [searchParams]);

  const currentMeta: RoleMeta = ROLE_METAS[activeRole as PrimaryPortalKey] || {
    key: activeRole,
    label: PORTALS[activeRole]?.label || activeRole,
    tabLabel: PORTALS[activeRole]?.shortTitle || activeRole,
    portalTitle: `${PORTALS[activeRole]?.label || activeRole} Portal`,
    quote:
      PORTALS[activeRole]?.description ||
      "Institutional workspace and operations.",
    badgeIcon: "🏛️",
    badgeLabel: PORTALS[activeRole]?.label || activeRole,
    identifierLabel:
      PORTALS[activeRole]?.identifierLabel || "USERNAME OR EMAIL",
    identifierPlaceholder:
      PORTALS[activeRole]?.identifierPlaceholder || "e.g. user@campusos.edu",
    identifierHint:
      PORTALS[activeRole]?.identifierHint ||
      "Use your institutional credentials.",
    ctaText: `Sign In to ${PORTALS[activeRole]?.label || activeRole} Portal →`,
    persona: {
      name: PORTALS[activeRole]?.label || "Campus Staff",
      roleTitle: PORTALS[activeRole]?.description || "Institutional User",
      avatarInitials: (PORTALS[activeRole]?.shortTitle || "CO").slice(0, 2),
      demoEmail: PORTALS[activeRole]?.demoEmail || "staff@campusos.edu",
      demoPassword: PORTALS[activeRole]?.demoPassword || "Password@123",
    },
  };

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If already authenticated, redirect directly to destination or dashboard
  useEffect(() => {
    if (!isLoading && user) {
      const redirectUrl = searchParams.get("redirect");
      if (
        redirectUrl &&
        redirectUrl.startsWith("/app") &&
        !redirectUrl.includes("//") &&
        !redirectUrl.includes("\\")
      ) {
        router.replace(redirectUrl);
      } else {
        router.replace("/app/dashboard");
      }
      if (typeof window !== "undefined") {
        const dest =
          redirectUrl &&
          redirectUrl.startsWith("/app") &&
          !redirectUrl.includes("//") &&
          !redirectUrl.includes("\\")
            ? redirectUrl
            : "/app/dashboard";
        setTimeout(() => {
          if (
            window.location.pathname === "/login" ||
            window.location.pathname === "/"
          ) {
            window.location.href = dest;
          }
        }, 350);
      }
    }
  }, [isLoading, user, router, searchParams]);

  const handleRoleSwitch = (roleKey: PortalKey) => {
    setActiveRole(roleKey);
    setErrorMessage(null);
  };

  const handleFillDemo = () => {
    setIdentifier(currentMeta.persona.demoEmail);
    setPassword(currentMeta.persona.demoPassword);
    setErrorMessage(null);
  };

  const handleDirectPersonaLaunch = async () => {
    setIdentifier(currentMeta.persona.demoEmail);
    setPassword(currentMeta.persona.demoPassword);
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const authenticatedUser = await login({
        email: currentMeta.persona.demoEmail,
        password: currentMeta.persona.demoPassword,
      });

      if (!authenticatedUser) {
        setErrorMessage("Authentication failed. Invalid username or password.");
        return;
      }

      // Role authorization verification
      const portalConfig = PORTALS[activeRole];
      if (portalConfig) {
        const roleSet = getNormalizedRoleSet(authenticatedUser);
        const isAuthorized =
          portalConfig.allowedRoles.some((r) => roleSet.has(r)) ||
          roleSet.has("SUPER_ADMIN");

        if (!isAuthorized) {
          await clearSession();
          setErrorMessage(
            `Authentication succeeded, but your account is not authorized for the ${portalConfig.label}. Please select the appropriate portal or contact your campus administrator.`,
          );
          return;
        }
      }

      const redirectUrl = searchParams.get("redirect");
      if (
        redirectUrl &&
        redirectUrl.startsWith("/app") &&
        !redirectUrl.includes("//") &&
        !redirectUrl.includes("\\")
      ) {
        router.replace(redirectUrl);
      } else {
        router.replace("/app/dashboard");
      }
      if (typeof window !== "undefined") {
        const dest =
          redirectUrl &&
          redirectUrl.startsWith("/app") &&
          !redirectUrl.includes("//") &&
          !redirectUrl.includes("\\")
            ? redirectUrl
            : "/app/dashboard";
        setTimeout(() => {
          if (
            window.location.pathname === "/login" ||
            window.location.pathname === "/"
          ) {
            window.location.href = dest;
          }
        }, 350);
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Authentication failed. Invalid username or password.";
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmedIdentifier = identifier.trim();
    if (!trimmedIdentifier) {
      setErrorMessage("Please enter your username or email address.");
      return;
    }

    if (!password) {
      setErrorMessage("Please enter your password.");
      return;
    }

    setIsSubmitting(true);

    try {
      const authenticatedUser = await login({
        email: trimmedIdentifier,
        password: password,
      });

      if (!authenticatedUser) {
        setErrorMessage("Authentication failed. Invalid username or password.");
        return;
      }

      // Role-Based Authorization Enforcement:
      // The selected portal is strictly an entry gateway. Verify actual roles from backend.
      const portalConfig = PORTALS[activeRole];
      if (portalConfig) {
        const roleSet = getNormalizedRoleSet(authenticatedUser);
        const isAuthorized =
          portalConfig.allowedRoles.some((r) => roleSet.has(r)) ||
          roleSet.has("SUPER_ADMIN");

        if (!isAuthorized) {
          // Immediately revoke session so unauthorized access is blocked
          await clearSession();
          setErrorMessage(
            `Authentication succeeded, but your account is not authorized for the ${portalConfig.label}. Please select the appropriate portal or contact your campus administrator.`,
          );
          return;
        }
      }

      const redirectUrl = searchParams.get("redirect");
      if (
        redirectUrl &&
        redirectUrl.startsWith("/app") &&
        !redirectUrl.includes("//") &&
        !redirectUrl.includes("\\")
      ) {
        router.replace(redirectUrl);
      } else {
        router.replace("/app/dashboard");
      }
      if (typeof window !== "undefined") {
        const dest =
          redirectUrl &&
          redirectUrl.startsWith("/app") &&
          !redirectUrl.includes("//") &&
          !redirectUrl.includes("\\")
            ? redirectUrl
            : "/app/dashboard";
        setTimeout(() => {
          if (
            window.location.pathname === "/login" ||
            window.location.pathname === "/"
          ) {
            window.location.href = dest;
          }
        }, 350);
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Authentication failed. Invalid username or password.";
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAF8F2]">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-amber-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-white selection:bg-amber-200 selection:text-slate-900 font-sans">
      {/* =========================================================================
          LEFT COLUMN: WARM IVORY GRADIENT (#FAF8F2)
          Minimalist institutional identity, headline, and compact highlights
          ========================================================================= */}
      <div className="w-full lg:w-[48%] xl:w-[46%] 2xl:w-[44%] bg-gradient-to-br from-[#FAF8F2] via-[#FAF8F2] to-[#F5EFEB] border-b lg:border-b-0 lg:border-r border-amber-200/50 p-8 sm:p-10 lg:p-12 xl:p-16 flex flex-col justify-between shrink-0 relative overflow-hidden">
        {/* Subtle decorative atmospheric warmth */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-amber-100/30 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-amber-100/20 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Section with Big Institutional Image from vsbec.edu.in */}
        <div className="space-y-4 relative z-10">
          <div className="relative w-full max-w-[380px] sm:max-w-[420px] h-20 sm:h-24 bg-white/95 p-3 rounded-2xl border border-amber-200/80 shadow-xs hover:shadow-sm transition-all overflow-hidden backdrop-blur-xs">
            <Image
              src="/vsb-college-header.jpg"
              alt="V.S.B. Engineering College (An Autonomous Institution)"
              fill
              className="object-contain object-left p-0.5"
              priority
            />
          </div>

          <div className="flex items-center gap-3 pt-1">
            <div className="relative h-10 w-10 shrink-0 rounded-full overflow-hidden border border-amber-200/90 bg-white p-0.5 shadow-2xs ring-2 ring-amber-100/60">
              <Image
                src="/college-logo.jpg"
                alt="VSB Engineering College Seal"
                fill
                className="object-contain rounded-full"
                priority
              />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 block font-sans">
                  CampusOS
                </span>
                <span className="px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase bg-amber-100 text-amber-900 border border-amber-300/80 rounded-full">
                  ERP V2.4
                </span>
              </div>
              <p className="text-xs font-medium text-slate-500 mt-0.5">
                V.S.B. Engineering College
              </p>
            </div>
          </div>
        </div>

        {/* Central Identity Section */}
        <div className="my-auto py-10 lg:py-14 space-y-6 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100/70 border border-amber-200 text-amber-900 shadow-2xs w-fit">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-600 animate-pulse" />
            <span className="text-[10px] sm:text-[11px] font-bold uppercase tracking-widest font-mono">
              ONE INSTITUTION. ONE DIGITAL ECOSYSTEM.
            </span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-[42px] xl:text-[46px] font-serif font-bold text-slate-900 leading-[1.18] tracking-tight">
            Everything Your Campus Needs.
            <br />
            <span className="text-amber-800">One Connected Platform.</span>
          </h1>

          <p className="text-sm sm:text-base text-slate-600 leading-relaxed max-w-lg">
            A unified digital workspace connecting students, faculty,
            departments and institutional administration.
          </p>
        </div>

        {/* Compact Functional Highlights */}
        <div className="pt-6 border-t border-amber-200/60 space-y-2.5 relative z-10">
          <p className="text-xs sm:text-sm font-semibold text-slate-800 tracking-wide">
            Academics · Attendance · Examinations · Finance · Administration
          </p>
          <p className="text-[11px] sm:text-xs text-slate-500">
            Secure Access · Role-Based Workspaces · Centralized Management
          </p>
        </div>
      </div>

      {/* =========================================================================
          RIGHT COLUMN: CLEAN WHITE CANVAS
          Top meta, 4-role segment bar, elevated login card & quick test persona
          ========================================================================= */}
      <div className="flex-1 flex flex-col justify-center px-6 sm:px-10 lg:px-12 xl:px-16 py-8 sm:py-10 bg-white relative">
        <div className="w-full max-w-xl mx-auto space-y-4 sm:space-y-5">
          {/* Top Meta Bar */}
          <div className="flex items-center justify-between text-[11px] font-semibold tracking-wider uppercase text-slate-400">
            <span>INSTITUTIONAL ACCESS PORTAL</span>
            <span className="font-mono text-slate-400">Tenant: VSB-CAMPUS</span>
          </div>

          {/* Main Heading */}
          <div className="space-y-1">
            <h2 className="text-2xl sm:text-3xl font-serif font-bold text-slate-900 tracking-tight">
              Select Your Portal Experience
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              Choose your role to load your authorized institutional workspace.
            </p>
          </div>

          {/* 4-Role Segment Bar */}
          <div className="grid grid-cols-4 gap-1.5 p-1.5 bg-slate-100/90 border border-slate-200/80 rounded-2xl shadow-2xs">
            {FOUR_ROLES.map((roleKey) => {
              const isActive = activeRole === roleKey;
              const meta = ROLE_METAS[roleKey];
              return (
                <button
                  key={roleKey}
                  type="button"
                  onClick={() => handleRoleSwitch(roleKey)}
                  className={cn(
                    "flex flex-col sm:flex-row items-center justify-center gap-1.5 py-2.5 px-2 rounded-xl text-xs transition-all duration-200 cursor-pointer select-none",
                    isActive
                      ? "bg-amber-400 text-slate-950 font-bold shadow-xs scale-[1.01]"
                      : "text-slate-600 hover:text-slate-950 hover:bg-white/80 font-medium",
                  )}
                  aria-label={`Select ${meta.label} Portal`}
                >
                  {roleKey === "STUDENT" && (
                    <GraduationCap className="h-4 w-4 shrink-0" />
                  )}
                  {roleKey === "FACULTY" && (
                    <Users className="h-4 w-4 shrink-0" />
                  )}
                  {roleKey === "VICE_PRINCIPAL" && (
                    <Landmark className="h-4 w-4 shrink-0" />
                  )}
                  {roleKey === "HOD" && (
                    <Building className="h-4 w-4 shrink-0" />
                  )}
                  <span className="truncate">{meta.tabLabel}</span>
                </button>
              );
            })}
          </div>

          {/* Elevated Login Card */}
          <div className="relative bg-white border border-slate-200/90 rounded-2xl shadow-sm hover:shadow-md transition-shadow p-6 sm:p-8 overflow-hidden">
            {/* Ambient Radial Warmth Glow */}
            <div className="absolute -top-16 -right-16 w-56 h-56 bg-amber-100/40 rounded-full blur-3xl pointer-events-none" />

            {/* Header Row: Academic Pill Badge & Fill Demo Trigger */}
            <div className="flex items-center justify-between relative z-10 mb-3">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-900 border border-amber-200/80 shadow-2xs">
                <span>{currentMeta.badgeIcon}</span>
                <span>{currentMeta.badgeLabel}</span>
              </div>

              <button
                type="button"
                onClick={handleFillDemo}
                className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 transition-all hover:scale-105 active:scale-95 shadow-2xs cursor-pointer"
              >
                <span>✨ Fill Demo</span>
              </button>
            </div>

            {/* Title & Quote */}
            <div className="relative z-10 mb-5">
              <h3 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                {currentMeta.portalTitle}
              </h3>
              <p className="text-xs italic text-slate-500 mt-1 font-serif">
                &ldquo;{currentMeta.quote}&rdquo;
              </p>
            </div>

            {/* Authentication Error Alert */}
            {errorMessage && (
              <div
                role="alert"
                className="mb-4 p-3.5 text-xs rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-start gap-2.5 animate-fade-in relative z-10"
              >
                <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
                <div className="leading-relaxed">{errorMessage}</div>
              </div>
            )}

            {/* Authentication Form */}
            <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
              {/* Field 1: Identifier */}
              <div>
                <label
                  htmlFor="identifier"
                  className="block text-[11px] font-bold uppercase tracking-wider text-slate-700 mb-1.5"
                >
                  {currentMeta.identifierLabel}
                </label>
                <Input
                  id="identifier"
                  name="identifier"
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder={currentMeta.identifierPlaceholder}
                  autoComplete="username"
                  required
                  className="h-11 text-sm rounded-xl border-slate-200 bg-white/90 focus:bg-white focus:border-amber-400 focus:ring-4 focus:ring-amber-400/15 transition-all shadow-2xs"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  {currentMeta.identifierHint}
                </p>
              </div>

              {/* Field 2: Password */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="password"
                    className="text-[11px] font-bold uppercase tracking-wider text-slate-700"
                  >
                    INSTITUTIONAL PASSWORD
                  </label>
                  <Link
                    href="/login/forgot-password"
                    className="text-xs font-semibold text-amber-700 hover:text-amber-900 hover:underline transition-colors"
                  >
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    autoComplete="current-password"
                    required
                    className="h-11 pr-10 text-sm rounded-xl border-slate-200 bg-white/90 focus:bg-white focus:border-amber-400 focus:ring-4 focus:ring-amber-400/15 transition-all shadow-2xs"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer transition-colors"
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Checkbox: Remember Me */}
              <div className="flex items-center gap-2 pt-1">
                <input
                  id="rememberMe"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-amber-500 focus:ring-amber-400 accent-amber-500 cursor-pointer"
                />
                <label
                  htmlFor="rememberMe"
                  className="text-xs text-slate-600 cursor-pointer select-none"
                >
                  Remember me on this institutional device
                </label>
              </div>

              {/* Golden Submit Button */}
              <div className="pt-1">
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full h-11 text-sm font-bold text-slate-950 bg-gradient-to-r from-amber-400 via-amber-400 to-yellow-400 hover:from-amber-500 hover:to-yellow-500 rounded-xl transition-all shadow-xs hover:shadow-md active:scale-[0.99] cursor-pointer flex items-center justify-center gap-2"
                  isLoading={isSubmitting}
                  disabled={isSubmitting}
                >
                  <span>{currentMeta.ctaText}</span>
                </Button>
              </div>
            </form>
          </div>

          {/* Quick-Switch Test Persona (Bottom Section) */}
          <div className="space-y-2 pt-1">
            <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <span>INSTANT TEST PERSONA</span>
              <span className="normal-case font-medium text-slate-400">
                1-Click Workspace Launch
              </span>
            </div>

            <div
              onClick={handleDirectPersonaLaunch}
              className="border border-slate-200/90 hover:border-amber-400/80 bg-gradient-to-r from-amber-50/30 via-white to-white hover:from-amber-50/60 rounded-2xl p-3.5 flex items-center justify-between transition-all cursor-pointer group shadow-2xs hover:shadow-sm"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-yellow-400 text-slate-950 font-bold text-xs flex items-center justify-center shrink-0 shadow-2xs ring-2 ring-white">
                  {currentMeta.persona.avatarInitials}
                </div>
                <div>
                  <div className="text-xs sm:text-sm font-semibold text-slate-900 group-hover:text-amber-950 transition-colors">
                    {currentMeta.persona.name}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {currentMeta.persona.roleTitle}
                  </div>
                </div>
              </div>
              <div className="text-xs font-semibold text-amber-900 bg-amber-100/80 group-hover:bg-amber-200 px-2.5 py-1 rounded-lg flex items-center gap-1 transition-all group-hover:translate-x-0.5">
                <span>Enter</span>
                <span>&gt;</span>
              </div>
            </div>
          </div>

          {/* Secondary Expander for Institutional Admin and Specialized Portals */}
          <div className="pt-1 text-center">
            <details className="group inline-block text-left">
              <summary className="text-[11px] font-medium text-slate-400 hover:text-slate-700 cursor-pointer inline-flex items-center gap-1 select-none">
                <span>
                  Looking for Admin or secondary campus portals? (Accounts,
                  Placement, Warden, etc.)
                </span>
                <span className="text-[9px] text-slate-400 group-open:rotate-180 transition-transform">
                  ▼
                </span>
              </summary>
              <div className="mt-2.5 p-2.5 bg-slate-50 border border-slate-200 rounded-xl grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-xs shadow-2xs">
                {/* Admin Portal option */}
                <button
                  type="button"
                  onClick={() => handleRoleSwitch("ADMIN")}
                  className={cn(
                    "flex items-center gap-2 p-2 rounded-lg border text-left transition-colors cursor-pointer",
                    activeRole === "ADMIN"
                      ? "bg-amber-100 border-amber-300 font-bold text-amber-900"
                      : "bg-white border-slate-200 hover:border-amber-300 text-slate-800",
                  )}
                >
                  <ShieldCheck className="h-4 w-4 text-amber-800 shrink-0" />
                  <span className="truncate">Admin Portal</span>
                </button>
                {/* Other specialized portals */}
                {ALL_PORTAL_KEYS.filter(
                  (k) => !FOUR_ROLES.includes(k as any) && k !== "ADMIN",
                ).map((k) => {
                  const p = PORTALS[k];
                  const isCur = activeRole === k;
                  return (
                    <button
                      key={k}
                      type="button"
                      onClick={() => handleRoleSwitch(k)}
                      className={cn(
                        "flex items-center gap-2 p-2 rounded-lg border text-left transition-colors cursor-pointer",
                        isCur
                          ? "bg-amber-100 border-amber-300 font-bold text-amber-900"
                          : "bg-white border-slate-200 hover:border-amber-300 text-slate-800",
                      )}
                    >
                      <div className="shrink-0">
                        {getRoleIcon(k, "h-3.5 w-3.5")}
                      </div>
                      <span className="truncate">{p.shortTitle}</span>
                    </button>
                  );
                })}
              </div>
            </details>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-[#FAF8F2]">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-amber-500" />
        </div>
      }
    >
      <LoginFormContent />
    </Suspense>
  );
}
