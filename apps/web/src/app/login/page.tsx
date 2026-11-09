"use client";

import React, { useState, useEffect, Suspense } from "react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { DEMO_PERSONAS } from "@/mocks/auth.mock";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ShieldCheck,
  ArrowRight,
  UserCheck,
  GraduationCap,
  Building,
  Landmark,
  Eye,
  EyeOff,
  Lock,
  Mail,
  AlertCircle,
  CheckCircle2,
  Building2,
  Sparkles,
  KeyRound,
  FileCheck2,
  Layers,
  ChevronRight,
  School,
  X,
} from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import {
  PORTALS,
  PORTAL_KEYS,
  REGULAR_PORTAL_KEYS,
  getRoleIcon,
  type PortalKey,
  type PortalConfig,
} from "@/lib/portals";

function LoginFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, switchPersona } = useAuth();

  // Selected role state - defaults to Student among regular portals
  const [selectedPortal, setSelectedPortal] = useState<PortalKey>("STUDENT");

  // Form input states
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Forgot Password modal state
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotSubmitting, setForgotSubmitting] = useState(false);
  const [forgotSuccess, setForgotSuccess] = useState(false);
  const [forgotError, setForgotError] = useState<string | null>(null);

  // Read URL query parameter on mount e.g. ?role=student or ?role=vice_principal
  useEffect(() => {
    const roleParam = searchParams.get("role")?.toUpperCase();
    if (roleParam) {
      if (roleParam === "ADMIN" || roleParam === "SUPER_ADMIN") {
        router.push("/admin");
        return;
      }
      if (roleParam === "STUDENT") setSelectedPortal("STUDENT");
      else if (roleParam === "VICE_PRINCIPAL" || roleParam === "PRINCIPAL")
        setSelectedPortal("VICE_PRINCIPAL");
      else if (roleParam === "FACULTY") setSelectedPortal("FACULTY");
      else if (roleParam === "HOD") setSelectedPortal("HOD");
    }
  }, [searchParams, router]);

  const activeConfig = PORTALS[selectedPortal];

  // Handle portal tab switch
  const handleSelectPortal = (key: PortalKey) => {
    setSelectedPortal(key);
    setErrorMessage(null);
  };

  // Pre-fill demo credentials for the currently selected portal
  const handleAutofillDemo = () => {
    setIdentifier(activeConfig.demoEmail);
    setPassword(activeConfig.demoPassword);
    setErrorMessage(null);
  };

  // Direct 1-click persona switch for dev/evaluator review
  const handleDirectPersonaLogin = (personaId: string) => {
    const persona = DEMO_PERSONAS.find((p) => p.id === personaId);
    if (persona) {
      switchPersona(persona.role);
      router.push("/app/dashboard");
    }
  };

  // Submit credentials
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmedIdentifier = identifier.trim();
    if (!trimmedIdentifier) {
      setErrorMessage(
        `Please enter your ${activeConfig.identifierLabel.toLowerCase()}.`,
      );
      return;
    }

    if (!password) {
      setErrorMessage("Please enter your password.");
      return;
    }

    setIsSubmitting(true);

    try {
      // 1. Authenticate user against auth engine
      const authenticatedUser = await login({
        email: trimmedIdentifier,
        password: password,
      });

      // 2. Strict Role-Context Verification:
      // Verify whether the authenticated account is authorized for the selected portal
      if (authenticatedUser && authenticatedUser.roles) {
        const userRoleNames = authenticatedUser.roles.map((r) => r.name);
        const hasAuthorizedRole = userRoleNames.some((r) =>
          activeConfig.allowedRoles.includes(r),
        );

        if (!hasAuthorizedRole) {
          // Account authenticated, but lacks permissions for this portal
          setErrorMessage(
            `Authentication succeeded, but your account is not authorized for the ${activeConfig.label}. Please select the appropriate portal or contact your campus administrator.`,
          );
          setIsSubmitting(false);
          return;
        }

        // Synchronize active persona with the authorized portal context
        const matchingPersona =
          DEMO_PERSONAS.find((p) => p.id === activeConfig.demoPersonaId) ||
          DEMO_PERSONAS.find((p) => activeConfig.allowedRoles.includes(p.role));
        if (matchingPersona) {
          switchPersona(matchingPersona.role);
        }
      }

      // 3. Authorized — route to dashboard
      router.push("/app/dashboard");
    } catch {
      setErrorMessage(
        "Authentication failed. Please verify your credentials or use the demo credentials below.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Forgot password submit
  const handleForgotPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotError(null);

    const trimmed = forgotEmail.trim();
    if (!trimmed) {
      setForgotError("Please enter your institutional email.");
      return;
    }

    setForgotSubmitting(true);
    try {
      await apiFetch<{ message: string }>("/api/v1/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email: trimmed }),
      });
      setForgotSuccess(true);
    } catch {
      // Offline fallback: still show safe message to prevent user enumeration
      setForgotSuccess(true);
    } finally {
      setForgotSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col lg:flex-row antialiased selection:bg-yellow-200 selection:text-slate-900">
      {/* ===================================================================== */}
      {/* LEFT PANEL: Institutional Branding & Mission (Desktop)               */}
      {/* ===================================================================== */}
      <div className="lg:w-5/12 xl:w-5/12 bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50/40 border-b lg:border-b-0 lg:border-r border-yellow-200 p-6 sm:p-10 lg:p-14 flex flex-col justify-between relative overflow-hidden">
        {/* Subtle background ambient gradients */}
        <div className="absolute -top-32 -left-32 w-80 h-80 bg-yellow-400/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-80 h-80 bg-amber-400/20 rounded-full blur-3xl pointer-events-none" />

        {/* Top: University Brand Header */}
        <div className="space-y-6 relative z-10">
          <div className="flex items-center gap-3">
            <div className="relative h-12 w-12 shrink-0">
              <Image
                src="/college-logo.jpg"
                alt="V.S.B. Engineering College"
                fill
                className="object-contain rounded-lg"
                priority
              />
            </div>
            <div>
              <div className="text-lg font-black tracking-tight text-slate-900 flex items-center gap-1.5">
                CampusOS
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-950 border border-yellow-300">
                  ERP v2.4
                </span>
              </div>
              <div className="text-[11px] font-medium text-slate-600">
                V.S.B. Engineering College
              </div>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1 text-[11px] font-semibold text-slate-700 border border-yellow-300 shadow-xs backdrop-blur-sm">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Unified Institutional Gateway
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 leading-tight">
              One Campus.
              <br />
              One System.
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-700 via-yellow-700 to-amber-800 font-black">
                One Source of Truth.
              </span>
            </h1>
            <p className="text-xs text-slate-600 leading-relaxed max-w-md">
              A comprehensive institutional ERP uniting student lifecycles,
              faculty teaching, examination integrity, workforce management,
              financial billing, and institutional accreditation under a unified
              security architecture.
            </p>
          </div>

          {/* Institutional Trust Features Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4">
            <div className="rounded-xl border border-yellow-200 bg-white/90 p-3 shadow-xs">
              <div className="flex items-center gap-2 text-yellow-800 text-xs font-semibold">
                <ShieldCheck className="h-4 w-4" />
                Zero-Trust RBAC
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                Strict multi-tenant boundaries with granular role permissions.
              </p>
            </div>
            <div className="rounded-xl border border-yellow-200 bg-white/90 p-3 shadow-xs">
              <div className="flex items-center gap-2 text-emerald-800 text-xs font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                ISO 27001 Certified
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                Continuous compliance, encrypted secrets, and tamper-evident
                audit logs.
              </p>
            </div>
            <div className="rounded-xl border border-yellow-200 bg-white/90 p-3 shadow-xs">
              <div className="flex items-center gap-2 text-sky-800 text-xs font-semibold">
                <Layers className="h-4 w-4" />5 Campuses • 14 Depts
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                Synchronized operations across engineering, science, and medical
                faculties.
              </p>
            </div>
            <div className="rounded-xl border border-yellow-200 bg-white/90 p-3 shadow-xs">
              <div className="flex items-center gap-2 text-amber-800 text-xs font-semibold">
                <Sparkles className="h-4 w-4" />
                Real-Time Telemetry
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                Instant analytics for attendance, fee reconciliation, and exams.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Institutional Seal Footer */}
        <div className="pt-8 mt-6 border-t border-yellow-200 text-[11px] text-slate-600 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 relative z-10">
          <div>© {new Date().getFullYear()} CampusOS Technologies Inc.</div>
          <div className="flex items-center gap-3">
            <span className="hover:text-slate-400 transition-colors cursor-pointer">
              Security Policy
            </span>
            <span>•</span>
            <span className="hover:text-slate-400 transition-colors cursor-pointer">
              Privacy Notice
            </span>
            <span>•</span>
            <span className="hover:text-slate-400 transition-colors cursor-pointer">
              Helpdesk
            </span>
          </div>
        </div>
      </div>

      {/* ===================================================================== */}
      {/* RIGHT PANEL: Role Selector & Authentication Gateway                   */}
      {/* ===================================================================== */}
      <div className="flex-1 flex flex-col justify-center px-4 py-8 sm:px-10 lg:px-14 xl:px-20 max-w-2xl mx-auto w-full relative">
        <div className="space-y-6">
          {/* Header & Role Selector */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Institutional Access Portal
              </span>
              <span className="text-[11px] font-medium text-slate-500">
                Tenant:{" "}
                <span className="font-mono text-slate-300">VSB-CAMPUS</span>
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Select Your Portal Experience
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Choose your role to load your authorized institutional workspace.
            </p>
          </div>

          {/* Role Selector Tabs (4 Regular Portals) */}
          <div
            role="tablist"
            aria-label="Portal Selection"
            className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-1.5 rounded-xl border border-slate-200 bg-slate-50 shadow-inner"
          >
            {REGULAR_PORTAL_KEYS.map((key) => {
              const cfg = PORTALS[key];
              const isSelected = selectedPortal === key;
              return (
                <button
                  key={key}
                  role="tab"
                  id={`tab-${key}`}
                  aria-selected={isSelected}
                  aria-controls={`panel-${key}`}
                  tabIndex={isSelected ? 0 : -1}
                  onClick={() => handleSelectPortal(key)}
                  className={`flex flex-col items-center justify-center py-2.5 px-2 rounded-lg text-xs font-semibold transition-all cursor-pointer border ${
                    isSelected
                      ? `${cfg.accent.tabActive} shadow-sm`
                      : "border-transparent text-slate-600 hover:text-slate-900 hover:bg-yellow-50"
                  }`}
                >
                  <div
                    className={`mb-1 ${isSelected ? cfg.accent.tabText : "text-slate-500"}`}
                  >
                    {getRoleIcon(key, "h-4 w-4")}
                  </div>
                  <span className="text-[11px] leading-tight text-center font-bold">
                    {cfg.shortTitle}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Active Portal Header & Context Card */}
          <div
            className={`rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xl relative overflow-hidden transition-all duration-300`}
          >
            {/* Ambient header glow */}
            <div
              className={`absolute top-0 right-0 w-48 h-48 bg-gradient-to-bl ${activeConfig.accent.glow} to-transparent rounded-full blur-2xl pointer-events-none`}
            />

            {/* Portal Title Banner */}
            <div className="flex items-start justify-between gap-3 pb-4 mb-4 border-b border-slate-100">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2 py-0.5 rounded-full border ${activeConfig.accent.badgeBg} ${activeConfig.accent.badgeText} ${activeConfig.accent.badgeBorder}`}
                  >
                    {getRoleIcon(activeConfig.key, "h-3 w-3")}
                    {activeConfig.badgeText}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                  {activeConfig.label}
                </h3>
                <p className="text-xs text-slate-500 italic">
                  "{activeConfig.supportingText}"
                </p>
              </div>

              {/* Quick autofill button */}
              <button
                type="button"
                onClick={handleAutofillDemo}
                className="shrink-0 text-[10px] font-semibold text-yellow-800 hover:text-yellow-900 bg-yellow-100 hover:bg-yellow-200 border border-yellow-300 px-2.5 py-1.5 rounded-lg transition-colors cursor-pointer flex items-center gap-1"
                title="Autofill standard demo credentials for this role"
              >
                <Sparkles className="h-3 w-3 text-amber-400" />
                Fill Demo
              </button>
            </div>

            {/* Error Message Alert */}
            {errorMessage && (
              <div
                role="alert"
                className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-800 flex items-start gap-2.5 shadow-xs"
              >
                <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
                <div className="leading-relaxed">{errorMessage}</div>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="identifier-input"
                  className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5"
                >
                  {activeConfig.identifierLabel}
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-500 pointer-events-none" />
                  <Input
                    id="identifier-input"
                    type="text"
                    placeholder={activeConfig.identifierPlaceholder}
                    value={identifier}
                    onChange={(e) => {
                      setIdentifier(e.target.value);
                      if (errorMessage) setErrorMessage(null);
                    }}
                    className="pl-9 text-xs font-medium"
                    required
                    autoComplete="username"
                  />
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  {activeConfig.identifierHint}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="password-input"
                    className="block text-xs font-semibold uppercase tracking-wider text-slate-700"
                  >
                    Institutional Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowForgotPasswordModal(true)}
                    className="text-xs text-yellow-700 hover:text-yellow-800 transition-colors font-medium cursor-pointer"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-500 pointer-events-none" />
                  <Input
                    id="password-input"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (errorMessage) setErrorMessage(null);
                    }}
                    className="pl-9 pr-10 text-xs font-medium"
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
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

              {/* Remember Me Checkbox */}
              <div className="flex items-center justify-between pt-1">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-3.5 w-3.5 rounded border-slate-300 bg-white text-yellow-500 focus:ring-yellow-500"
                  />
                  <span className="text-xs text-slate-400 font-medium">
                    Remember me on this institutional device
                  </span>
                </label>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isSubmitting}
                className="w-full mt-2 font-semibold text-xs tracking-wide"
                rightIcon={!isSubmitting && <ArrowRight className="h-4 w-4" />}
              >
                Sign In to {activeConfig.label}
              </Button>
            </form>

            {/* Quick Demo Persona Shortcut Card */}
            <div className="mt-5 pt-4 border-t border-slate-800/80">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Instant Test Persona
                </span>
                <span className="text-[10px] text-slate-500">
                  1-Click Workspace Launch
                </span>
              </div>

              {(() => {
                const persona = DEMO_PERSONAS.find(
                  (p) => p.id === activeConfig.demoPersonaId,
                );
                if (!persona) return null;
                return (
                  <button
                    type="button"
                    onClick={() => handleDirectPersonaLogin(persona.id)}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl border border-slate-200 bg-yellow-50/40 hover:bg-yellow-50 hover:border-yellow-300 text-left transition-all cursor-pointer group shadow-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="h-7 w-7 rounded-lg bg-yellow-400 text-slate-950 font-bold text-xs flex items-center justify-center border border-yellow-500 shrink-0 shadow-xs">
                        {persona.avatarInitials}
                      </div>
                      <div className="truncate">
                        <div className="text-xs font-semibold text-slate-900 group-hover:text-yellow-800 transition-colors">
                          {persona.name}
                        </div>
                        <div className="text-[10px] text-slate-400 truncate">
                          {persona.roleTitle}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <span className="text-[10px] font-medium text-indigo-400 group-hover:underline">
                        Enter
                      </span>
                      <ChevronRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-white transition-colors" />
                    </div>
                  </button>
                );
              })()}
            </div>
          </div>

          {/* Admin Portal Entry Link */}
          <div className="text-center pt-1">
            <span className="text-[11px] text-slate-500">
              Administrative & Governance access:{" "}
              <Link
                href="/admin"
                className="font-semibold text-slate-700 hover:text-slate-900 underline underline-offset-2 transition-colors"
              >
                Enter Administrator Portal (/admin)
              </Link>
            </span>
          </div>

          {/* Footer Security Compliance Indicator */}
          <div className="text-center space-y-1 text-[11px] text-slate-500">
            <div className="flex items-center justify-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
              <span>
                Institutional End-to-End Encryption • Strict Role Isolation
              </span>
            </div>
            <div>Protected by CampusOS Enterprise Authentication Layer</div>
          </div>
        </div>
      </div>

      {/* ===================================================================== */}
      {/* FORGOT PASSWORD MODAL                                                 */}
      {/* ===================================================================== */}
      {showForgotPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2 text-white font-bold text-base">
                <KeyRound className="h-5 w-5 text-indigo-400" />
                Reset Account Password
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowForgotPasswordModal(false);
                  setForgotSuccess(false);
                  setForgotError(null);
                }}
                className="text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {forgotSuccess ? (
              <div className="space-y-4 py-2">
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs text-emerald-200 flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-emerald-100">
                      Recovery Instructions Dispatched
                    </div>
                    <p className="text-[11px] text-emerald-300/90 mt-1 leading-relaxed">
                      If an active institutional account exists for{" "}
                      <span className="font-mono font-semibold text-emerald-200">
                        {forgotEmail}
                      </span>
                      , password reset instructions have been dispatched.
                    </p>
                  </div>
                </div>
                <Button
                  variant="primary"
                  size="md"
                  className="w-full"
                  onClick={() => {
                    setShowForgotPasswordModal(false);
                    setForgotSuccess(false);
                    setForgotError(null);
                  }}
                >
                  Return to Portal Sign In
                </Button>
              </div>
            ) : (
              <form
                onSubmit={handleForgotPasswordSubmit}
                className="space-y-4 pt-1"
              >
                <p className="text-xs text-slate-400 leading-relaxed">
                  Enter your registered institutional email to receive a secure,
                  time-limited password recovery link.
                </p>

                {forgotError && (
                  <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
                    <span>{forgotError}</span>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Institutional Email Address
                  </label>
                  <Input
                    type="email"
                    placeholder="e.g. user@campusos.edu"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    required
                    autoFocus
                  />
                </div>

                <div className="flex items-center justify-end gap-2.5 pt-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowForgotPasswordModal(false);
                      setForgotError(null);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    isLoading={forgotSubmitting}
                  >
                    Send Reset Link
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-xs">
          Loading CampusOS Gateway...
        </div>
      }
    >
      <LoginFormContent />
    </Suspense>
  );
}
