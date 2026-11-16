"use client";

import React, { useState, useEffect, Suspense } from "react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Eye, EyeOff, AlertCircle } from "lucide-react";

function LoginFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoading, login } = useAuth();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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
      <div className="w-full max-w-sm sm:max-w-md bg-white rounded-xl border border-slate-200/90 shadow-sm p-6 sm:p-8">
        {/* 1. CampusOS Logo & Brand Name */}
        <div className="flex items-center justify-center gap-2.5 mb-6">
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

        {/* 2. Login Heading */}
        <h1 className="text-xl font-semibold text-slate-900 text-center mb-6 tracking-tight">
          Sign in to your account
        </h1>

        {/* 8. Authentication Error Message */}
        {errorMessage && (
          <div
            role="alert"
            className="mb-5 p-3 text-xs rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-2.5"
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
              Username or Email
            </label>
            <Input
              id="identifier"
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="name@campusos.edu or username"
              autoComplete="username"
              required
              className="h-10 text-sm"
            />
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
        </form>
      </div>
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
