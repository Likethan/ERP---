"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, CheckCircle2, AlertCircle } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmed = email.trim();
    if (!trimmed) {
      setErrorMessage("Please enter your institutional email address.");
      return;
    }

    if (!trimmed.includes("@") || !trimmed.includes(".")) {
      setErrorMessage("Please enter a valid email address.");
      return;
    }

    setIsSubmitting(true);
    try {
      await apiFetch<{ message: string }>("/api/v1/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email: trimmed }),
      });
      setIsSuccess(true);
    } catch {
      // In offline/demo mode, still show safe generic message to avoid account discovery
      setIsSuccess(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 p-4 sm:p-6 antialiased selection:bg-yellow-200 selection:text-slate-900">
      <div className="w-full max-w-sm sm:max-w-md bg-white rounded-xl border border-slate-200/90 shadow-sm p-6 sm:p-8">
        {/* Brand Header */}
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

        {/* Heading */}
        <div className="text-center mb-6">
          <h1 className="text-xl font-semibold text-slate-900 tracking-tight">
            Reset your password
          </h1>
          <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
            Enter your registered institutional email to receive a secure
            password reset link.
          </p>
        </div>

        {isSuccess ? (
          <div className="space-y-4">
            <div className="p-4 text-xs rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-start gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold text-emerald-950">
                  Recovery instructions sent
                </div>
                <p className="text-[11px] text-emerald-800/90 leading-relaxed">
                  If an active account exists for{" "}
                  <span className="font-medium text-emerald-950">{email}</span>,
                  password reset instructions have been dispatched.
                </p>
              </div>
            </div>

            <div className="pt-2">
              <Link href="/login" className="block w-full">
                <Button
                  variant="primary"
                  size="md"
                  className="w-full h-10 font-semibold cursor-pointer"
                >
                  Return to Sign In
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {errorMessage && (
              <div
                role="alert"
                className="p-3 text-xs rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-2.5"
              >
                <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
                <div className="leading-relaxed">{errorMessage}</div>
              </div>
            )}

            <div className="space-y-1.5">
              <label
                htmlFor="reset-email"
                className="block text-xs font-medium text-slate-700"
              >
                Institutional Email Address
              </label>
              <Input
                id="reset-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@campusos.edu"
                required
                autoFocus
                className="h-10 text-sm"
              />
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full h-10 font-semibold cursor-pointer"
                isLoading={isSubmitting}
                disabled={isSubmitting}
              >
                Send Reset Link
              </Button>
            </div>

            <div className="pt-2 text-center">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to Sign In
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
