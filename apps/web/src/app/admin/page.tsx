"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { DEMO_PERSONAS } from "@/mocks/auth.mock";
import { PORTALS } from "@/lib/portals";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ShieldCheck,
  ArrowRight,
  Lock,
  Mail,
  AlertCircle,
  Eye,
  EyeOff,
  School,
  KeyRound,
  CheckCircle2,
  X,
  ArrowLeft,
} from "lucide-react";
import { apiFetch } from "@/lib/api-client";

export default function AdminPortalPage() {
  const router = useRouter();
  const { user, login, switchPersona, logout } = useAuth();
  const adminConfig = PORTALS.ADMIN;

  // Form input states
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Forgot password modal
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotSubmitting, setForgotSubmitting] = useState(false);
  const [forgotSuccess, setForgotSuccess] = useState(false);
  const [forgotError, setForgotError] = useState<string | null>(null);

  const isUserAdmin = Boolean(
    user?.roles?.some((r) => adminConfig.allowedRoles.includes(r.name)) ||
    user?.permissions?.includes("*"),
  );

  const handleAutofillDemo = () => {
    setIdentifier(adminConfig.demoEmail);
    setPassword(adminConfig.demoPassword);
    setErrorMessage(null);
  };

  const handleDirectPersonaLogin = () => {
    const adminPersona = DEMO_PERSONAS.find(
      (p) => p.id === adminConfig.demoPersonaId || p.role === "SUPER_ADMIN",
    );
    if (adminPersona) {
      switchPersona(adminPersona.role);
      router.push("/app/dashboard");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmedIdentifier = identifier.trim();
    if (!trimmedIdentifier) {
      setErrorMessage("Please enter your institutional administrator email.");
      return;
    }

    if (!password) {
      setErrorMessage("Please enter your administrator password.");
      return;
    }

    setIsSubmitting(true);

    try {
      const authenticatedUser = await login({
        email: trimmedIdentifier,
        password: password,
      });

      if (authenticatedUser && authenticatedUser.roles) {
        const userRoleNames = authenticatedUser.roles.map((r) => r.name);
        const hasAuthorizedRole = userRoleNames.some((r) =>
          adminConfig.allowedRoles.includes(r),
        );

        if (!hasAuthorizedRole) {
          setErrorMessage(
            "Authentication succeeded, but your account is not authorized for the Administrator Portal. Please log in with authorized administrator credentials.",
          );
          setIsSubmitting(false);
          return;
        }

        const adminPersona =
          DEMO_PERSONAS.find((p) => p.id === adminConfig.demoPersonaId) ||
          DEMO_PERSONAS.find((p) => p.role === "SUPER_ADMIN");
        if (adminPersona) {
          switchPersona(adminPersona.role);
        }
      }

      router.push("/app/dashboard");
    } catch {
      setErrorMessage(
        "Authentication failed. Please verify your credentials or use the demo credentials below.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForgotPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotError(null);

    const trimmed = forgotEmail.trim();
    if (!trimmed) {
      setForgotError("Please enter your institutional administrator email.");
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
      setForgotSuccess(true);
    } finally {
      setForgotSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col lg:flex-row antialiased selection:bg-yellow-200 selection:text-slate-900">
      {/* LEFT PANEL: Institutional Governance Branding */}
      <div className="lg:w-5/12 xl:w-5/12 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 text-white p-6 sm:p-10 lg:p-14 flex flex-col justify-between relative overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800">
        <div className="absolute -top-32 -left-32 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-80 h-80 bg-yellow-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="space-y-6 relative z-10">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-yellow-400 text-slate-950 flex items-center justify-center shadow-md border border-yellow-500">
              <School className="h-5 w-5 text-slate-950" />
            </div>
            <div>
              <div className="text-lg font-black tracking-tight text-white flex items-center gap-1.5">
                CampusOS
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700">
                  Admin Gateway
                </span>
              </div>
              <div className="text-[11px] font-medium text-slate-400">
                Institutional Administration & Governance
              </div>
            </div>
          </div>

          <div className="space-y-3 pt-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-slate-800/80 px-3 py-1 text-[11px] font-semibold text-emerald-300 border border-slate-700 shadow-xs backdrop-blur-sm">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              Restricted Administrative Access
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white leading-tight">
              Administrator
              <br />
              <span className="text-yellow-400">Command Portal</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed pt-1">
              Dedicated institutional gateway for Registrars, Institutional
              Administrators, and System IAM Operators. Manage configuration,
              master records, security policies, and audit trails.
            </p>
          </div>

          <div className="pt-6 border-t border-slate-800/80 space-y-3">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Administrative Capabilities
            </div>
            <ul className="text-xs text-slate-300 space-y-2">
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Enterprise Security, IAM, and Role-Based Access Control
              </li>
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Master Institutional Structure, Campuses & Departments
              </li>
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Immutable Audit Trails, Statutory Reporting & Compliance
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-8 mt-6 border-t border-slate-800 text-[11px] text-slate-400 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 relative z-10">
          <div>© {new Date().getFullYear()} CampusOS Technologies Inc.</div>
          <Link
            href="/login"
            className="inline-flex items-center gap-1.5 text-yellow-400 hover:text-yellow-300 font-medium transition-colors"
          >
            <ArrowLeft className="h-3 w-3" />
            <span>Regular Portals (Student, Faculty, VP, HOD)</span>
          </Link>
        </div>
      </div>

      {/* RIGHT PANEL: Administrator Sign-In Flow */}
      <div className="flex-1 flex flex-col justify-center px-4 py-8 sm:px-10 lg:px-14 xl:px-20 max-w-2xl mx-auto w-full relative">
        <div className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Institutional Security Gateway
              </span>
              <span className="text-[11px] font-medium text-slate-500">
                Route: <span className="font-mono text-slate-700">/admin</span>
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Administrator Portal Sign-In
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              {adminConfig.supportingText}
            </p>
          </div>

          {/* Active Admin Session Status Banner */}
          {user && (
            <div
              className={`rounded-xl border p-4 text-xs ${
                isUserAdmin
                  ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                  : "border-amber-300 bg-amber-50 text-amber-900"
              }`}
            >
              <div className="flex items-start gap-3">
                {isUserAdmin ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="font-bold">
                    {isUserAdmin
                      ? "Active Administrator Session Detected"
                      : "Account Lacks Administrator Authorization"}
                  </div>
                  <p className="text-[11px] mt-0.5">
                    Currently signed in as:{" "}
                    <span className="font-semibold">{user.email}</span> (Role:{" "}
                    {user.roles?.[0]?.name || "None"})
                  </p>
                  <div className="mt-3 flex items-center gap-3">
                    {isUserAdmin ? (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => router.push("/app/dashboard")}
                        className="bg-yellow-400 hover:bg-yellow-500 text-slate-950 font-bold"
                      >
                        Enter Admin Dashboard
                        <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                      </Button>
                    ) : (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => logout()}
                        className="border-amber-300 text-amber-900 hover:bg-amber-100"
                      >
                        Sign Out & Switch Account
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Admin Sign-In Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xl relative overflow-hidden">
            <div className="flex items-start justify-between gap-3 pb-4 mb-4 border-b border-slate-100">
              <div>
                <h3 className="font-bold text-slate-900 text-base">
                  {adminConfig.label}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {adminConfig.identifierHint}
                </p>
              </div>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-900 border border-emerald-200">
                {adminConfig.badgeText}
              </span>
            </div>

            {/* Error Message Alert */}
            {errorMessage && (
              <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-xs text-rose-900 flex items-start gap-2.5">
                <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
                <div className="flex-1 font-medium">{errorMessage}</div>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="admin-email"
                  className="block text-xs font-semibold text-slate-700 mb-1.5"
                >
                  {adminConfig.identifierLabel}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Mail className="h-4 w-4" />
                  </div>
                  <Input
                    id="admin-email"
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => {
                      setIdentifier(e.target.value);
                      setErrorMessage(null);
                    }}
                    placeholder={adminConfig.identifierPlaceholder}
                    className="pl-9 h-11 text-xs border-slate-200 focus:border-yellow-400 focus:ring-yellow-400/20"
                    autoComplete="username"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="admin-password"
                    className="block text-xs font-semibold text-slate-700"
                  >
                    Administrator Password
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setForgotEmail(identifier);
                      setShowForgotPasswordModal(true);
                    }}
                    className="text-xs text-yellow-700 hover:text-yellow-800 font-medium cursor-pointer"
                  >
                    Forgot Password?
                  </button>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock className="h-4 w-4" />
                  </div>
                  <Input
                    id="admin-password"
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      setErrorMessage(null);
                    }}
                    placeholder="Enter administrative credentials"
                    className="pl-9 pr-10 h-11 text-xs border-slate-200 focus:border-yellow-400 focus:ring-yellow-400/20"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
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

              <div className="flex items-center justify-between pt-1">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-yellow-500 focus:ring-yellow-400"
                  />
                  <span className="text-xs text-slate-600">
                    Remember this administrative workstation
                  </span>
                </label>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="lg"
                disabled={isSubmitting}
                className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-950 font-bold border border-yellow-500/60 shadow-xs h-11"
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950 border-t-transparent" />
                    Authenticating Administrator...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <span>Sign In to Administrator Portal</span>
                    <ArrowRight className="h-4 w-4" />
                  </span>
                )}
              </Button>
            </form>

            {/* Quick Demo Credentials Autofill */}
            <div className="mt-5 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-2.5">
              <button
                type="button"
                onClick={handleAutofillDemo}
                className="text-xs font-semibold text-slate-700 hover:text-slate-950 underline underline-offset-2 flex items-center gap-1.5 cursor-pointer"
              >
                <KeyRound className="h-3.5 w-3.5 text-yellow-600" />
                <span>Autofill Demo Credentials ({adminConfig.demoEmail})</span>
              </button>

              <button
                type="button"
                onClick={handleDirectPersonaLogin}
                className="text-xs font-bold text-slate-900 bg-yellow-100 hover:bg-yellow-200 border border-yellow-300 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
              >
                1-Click Admin Access
              </button>
            </div>
          </div>

          <div className="text-center pt-2">
            <span className="text-xs text-slate-500">
              Not an institutional administrator?{" "}
              <Link
                href="/login"
                className="font-semibold text-slate-800 hover:text-slate-950 underline underline-offset-2"
              >
                Return to Regular Portals
              </Link>
            </span>
          </div>
        </div>
      </div>

      {/* FORGOT PASSWORD MODAL */}
      {showForgotPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2 text-white font-bold text-base">
                <KeyRound className="h-5 w-5 text-indigo-400" />
                Reset Administrator Password
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
                      If an active institutional administrator account exists
                      for{" "}
                      <span className="font-mono font-semibold text-emerald-200">
                        {forgotEmail}
                      </span>
                      , security credentials reset instructions have been
                      dispatched.
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
                  }}
                >
                  Return to Admin Sign-In
                </Button>
              </div>
            ) : (
              <form onSubmit={handleForgotPasswordSubmit} className="space-y-4">
                <p className="text-xs text-slate-300">
                  Enter your registered institutional administrator email to
                  receive secure password recovery instructions.
                </p>
                {forgotError && (
                  <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-2.5 rounded-lg">
                    {forgotError}
                  </div>
                )}
                <div>
                  <label
                    htmlFor="admin-forgot-email"
                    className="block text-xs font-semibold text-slate-300 mb-1"
                  >
                    Institutional Administrator Email
                  </label>
                  <Input
                    id="admin-forgot-email"
                    type="email"
                    required
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="e.g. registrar@campusos.edu"
                    className="bg-slate-800 border-slate-700 text-white text-xs h-10"
                  />
                </div>
                <div className="flex items-center justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-slate-400 hover:text-white"
                    onClick={() => setShowForgotPasswordModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    disabled={forgotSubmitting}
                    className="bg-yellow-400 hover:bg-yellow-500 text-slate-950 font-semibold"
                  >
                    {forgotSubmitting ? "Dispatching..." : "Send Reset Link"}
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
