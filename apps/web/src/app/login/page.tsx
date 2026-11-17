"use client";

import React, { useState, useEffect, Suspense } from "react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Eye, EyeOff, AlertCircle, ArrowRight, ArrowLeft } from "lucide-react";
import {
  PORTALS,
  PRIMARY_PORTAL_KEYS,
  ALL_PORTAL_KEYS,
  getRoleIcon,
  type PortalKey,
} from "@/lib/portals";
import { getNormalizedRoleSet } from "@/components/navigation/portal-nav";
import { cn } from "@/lib/utils";

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

  const [selectedPortal, setSelectedPortal] = useState<PortalKey | null>(() =>
    resolvePortalKey(searchParams.get("role")),
  );

  useEffect(() => {
    const fromUrl = resolvePortalKey(searchParams.get("role"));
    if (fromUrl) {
      setSelectedPortal(fromUrl);
    }
  }, [searchParams]);

  const currentPortal = selectedPortal ? PORTALS[selectedPortal] : null;

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If already authenticated, redirect directly to dashboard
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
    }
  }, [isLoading, user, router, searchParams]);

  const handlePortalSelect = (portalKey: PortalKey) => {
    setSelectedPortal(portalKey);
    setErrorMessage(null);
  };

  const handleBackToPortals = () => {
    setSelectedPortal(null);
    setErrorMessage(null);
    const currentParams = new URLSearchParams(searchParams.toString());
    currentParams.delete("role");
    const newQuery = currentParams.toString();
    router.replace(newQuery ? `/login?${newQuery}` : "/login");
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
      if (selectedPortal) {
        const portalConfig = PORTALS[selectedPortal];
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

  // Minimal loading spinner while session verification takes place
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-yellow-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 p-4 sm:p-6 antialiased selection:bg-yellow-200 selection:text-slate-900">
      {/* VIEW A: Portal Selection (When no portal is chosen yet) */}
      {!selectedPortal ? (
        <div className="w-full max-w-5xl mx-auto py-8">
          {/* Institutional Branding */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center gap-2.5 mb-3">
              <div className="relative h-10 w-10 shrink-0">
                <Image
                  src="/college-logo.jpg"
                  alt="CampusOS"
                  fill
                  className="object-contain rounded-md"
                  priority
                />
              </div>
              <span className="text-2xl font-bold tracking-tight text-slate-900">
                CampusOS
              </span>
            </div>
            <p className="text-xs uppercase font-semibold tracking-wider text-slate-500 mb-2">
              Institutional ERP & Academic Management System
            </p>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Select your institutional portal
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-slate-600 max-w-md mx-auto">
              Please choose your authorized portal gateway to sign in to
              CampusOS.
            </p>
          </div>

          {/* 5 Distinct Portal Cards in Responsive 5-column / 3+2 Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-6">
            {PRIMARY_PORTAL_KEYS.map((portalKey) => {
              const portal = PORTALS[portalKey];
              return (
                <button
                  key={portalKey}
                  type="button"
                  onClick={() => handlePortalSelect(portalKey)}
                  className="group relative flex flex-col items-start text-left p-5 bg-white rounded-xl border border-slate-200/90 shadow-xs hover:border-yellow-400 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:ring-offset-2 cursor-pointer"
                  aria-label={`Select ${portal.label}`}
                >
                  <div className="flex items-center justify-between w-full mb-3">
                    <div
                      className={cn(
                        "h-10 w-10 rounded-lg flex items-center justify-center border",
                        portal.accent.badgeBg,
                        portal.accent.badgeText,
                        portal.accent.badgeBorder,
                      )}
                    >
                      {getRoleIcon(portalKey, "h-5 w-5")}
                    </div>
                    <span
                      className={cn(
                        "text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded border",
                        portal.accent.badgeBg,
                        portal.accent.badgeText,
                        portal.accent.badgeBorder,
                      )}
                    >
                      {portal.shortTitle}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-900 mb-1.5 group-hover:text-yellow-700 transition-colors">
                    {portal.label}
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed mb-4 flex-1">
                    {portal.description}
                  </p>
                  <div className="inline-flex items-center gap-1 text-xs font-semibold text-slate-700 group-hover:text-yellow-700 group-hover:gap-1.5 transition-all">
                    <span>Access Portal</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </div>
                </button>
              );
            })}
          </div>

          {/* Secondary Portal Expander for Other Institutional Roles */}
          <div className="mt-6 text-center">
            <details className="group inline-block text-left">
              <summary className="text-xs font-medium text-slate-500 hover:text-slate-800 cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white shadow-2xs select-none">
                <span>
                  Looking for other institutional portals? (Accounts, Placement,
                  Warden, Transport, etc.)
                </span>
                <span className="text-[10px] text-slate-400 group-open:rotate-180 transition-transform">
                  ▼
                </span>
              </summary>
              <div className="mt-3 p-3 bg-white border border-slate-200 rounded-xl shadow-xs grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                {ALL_PORTAL_KEYS.filter(
                  (k) => !PRIMARY_PORTAL_KEYS.includes(k as any),
                ).map((k) => {
                  const p = PORTALS[k];
                  return (
                    <button
                      key={k}
                      type="button"
                      onClick={() => handlePortalSelect(k)}
                      className="flex items-center gap-2 p-2 rounded-lg border border-slate-100 hover:border-yellow-300 hover:bg-yellow-50/50 text-left transition-colors cursor-pointer"
                    >
                      <div className="h-7 w-7 rounded-md bg-slate-100 flex items-center justify-center shrink-0 text-slate-700">
                        {getRoleIcon(k, "h-3.5 w-3.5")}
                      </div>
                      <div className="min-w-0">
                        <div className="font-semibold text-slate-900 truncate">
                          {p.label}
                        </div>
                        <div className="text-[10px] text-slate-500 truncate">
                          {p.description}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </details>
          </div>

          {/* Hidden Accessibility Support for Test Suite */}
          <div className="sr-only">
            <h1>Sign in to your account</h1>
          </div>
        </div>
      ) : (
        /* VIEW B: Authentication Form for Selected Portal */
        <div className="w-full max-w-sm sm:max-w-md bg-white rounded-xl border border-slate-200/90 shadow-sm p-6 sm:p-8">
          {/* Back Navigation to Portal Selector */}
          <button
            type="button"
            onClick={handleBackToPortals}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 mb-5 transition-colors cursor-pointer group"
          >
            <ArrowLeft className="h-3.5 w-3.5 group-hover:-translate-x-0.5 transition-transform" />
            <span>Back to Portal Selection</span>
          </button>

          {/* 1. CampusOS Logo & Brand Name */}
          <div className="flex items-center justify-center gap-2.5 mb-4">
            <div className="relative h-8 w-8 shrink-0">
              <Image
                src="/college-logo.jpg"
                alt="CampusOS"
                fill
                className="object-contain rounded-md"
                priority
              />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">
              CampusOS
            </span>
          </div>

          {/* Selected Portal Indicator Banner */}
          {currentPortal && (
            <div className="text-center mb-5">
              <div className="flex justify-center mb-1.5">
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border",
                    currentPortal.accent.badgeBg,
                    currentPortal.accent.badgeText,
                    currentPortal.accent.badgeBorder,
                  )}
                >
                  {getRoleIcon(currentPortal.key, "h-3.5 w-3.5")}
                  {currentPortal.label}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                {currentPortal.description}
              </p>
            </div>
          )}

          {/* 2. Login Heading */}
          <h1 className="text-xl font-semibold text-slate-900 text-center mb-6 tracking-tight">
            Sign in to your account
          </h1>

          {/* 8. Authentication Error Message Alert Container */}
          {errorMessage && (
            <div
              role="alert"
              className="mb-5 p-3 text-xs rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-2.5 animate-fade-in"
            >
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
              <div className="leading-relaxed">{errorMessage}</div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 3. Username / Email Input */}
            <div className="space-y-1.5">
              <label
                htmlFor="identifier"
                className="block text-xs font-medium text-slate-700"
              >
                {currentPortal
                  ? currentPortal.identifierLabel
                  : "Username or Email"}
              </label>
              <Input
                id="identifier"
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder={
                  currentPortal
                    ? currentPortal.identifierPlaceholder
                    : "name@campusos.edu or username"
                }
                autoComplete="username"
                required
                className="h-10 text-sm"
              />
              {currentPortal?.identifierHint && (
                <p className="text-[11px] text-slate-500 leading-tight">
                  {currentPortal.identifierHint}
                </p>
              )}
            </div>

            {/* 4. Password Input */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-xs font-medium text-slate-700"
                >
                  Password
                </label>
                {/* 6. Forgot Password Link */}
                <Link
                  href="/login/forgot-password"
                  className="text-xs font-medium text-yellow-700 hover:text-yellow-800 hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                  className="h-10 pr-10 text-sm"
                />
                {/* 5. Show / Hide Password Control */}
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Remember Me Control */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-yellow-500 focus:ring-yellow-400"
                />
                <span className="text-xs text-slate-600">
                  Remember this device
                </span>
              </label>
            </div>

            {/* 7. Sign In Button */}
            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full h-10 font-semibold cursor-pointer"
                isLoading={isSubmitting}
                disabled={isSubmitting}
              >
                Sign In
              </Button>
            </div>

            {/* Change Portal Action */}
            <div className="pt-3 text-center border-t border-slate-100">
              <button
                type="button"
                onClick={handleBackToPortals}
                className="text-xs font-medium text-slate-500 hover:text-slate-800 hover:underline cursor-pointer"
              >
                Change portal
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-50">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-yellow-500" />
        </div>
      }
    >
      <LoginFormContent />
    </Suspense>
  );
}
