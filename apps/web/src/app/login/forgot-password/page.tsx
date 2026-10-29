"use client";

import React, { useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ShieldCheck,
  ArrowLeft,
  Mail,
  CheckCircle2,
  AlertCircle,
  KeyRound,
  Building2,
} from "lucide-react";

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
      // In offline/demo mode or network fallback, still show generic safe success message to avoid account discovery
      setIsSuccess(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4 py-12 sm:px-6 lg:px-8 text-slate-100">
      <div className="w-full max-w-md space-y-6">
        {/* Brand & Institution Badge */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            Institutional Security Gateway
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center justify-center gap-2">
            <Building2 className="h-6 w-6 text-indigo-400" />
            CampusOS
          </h1>
          <p className="text-xs text-slate-400">
            One Campus. One System. One Source of Truth.
          </p>
        </div>

        {/* Card Box */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 sm:p-8 shadow-2xl backdrop-blur-sm">
          <div className="mb-6">
            <div className="inline-flex p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-3">
              <KeyRound className="h-5 w-5" />
            </div>
            <h2 className="text-lg font-bold text-white">Reset Account Password</h2>
            <p className="text-xs text-slate-400 mt-1">
              Enter your registered institutional email to receive a secure, time-limited password reset link.
            </p>
          </div>

          {isSuccess ? (
            <div className="space-y-4">
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs text-emerald-200 flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="font-semibold text-emerald-100">Recovery Instructions Dispatched</div>
                  <p className="text-[11px] text-emerald-300/90 leading-relaxed">
                    If an active institutional account exists for <span className="font-mono font-semibold text-emerald-200">{email}</span>, password reset instructions have been dispatched. Please inspect your institutional inbox and spam filter.
                  </p>
                </div>
              </div>

              <div className="pt-2">
                <Link href="/login" className="block w-full">
                  <Button variant="primary" size="md" className="w-full">
                    Return to Login Portal
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {errorMessage && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-400 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Institutional Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                  <Input
                    type="email"
                    placeholder="e.g. user@campusos.edu or student@campusos.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-9 text-xs"
                    required
                    autoFocus
                  />
                </div>
                <p className="text-[10px] text-slate-500 mt-1">
                  Must be the email linked to your institutional student, faculty, or staff profile.
                </p>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isSubmitting}
                className="w-full mt-2"
              >
                Send Password Reset Instructions
              </Button>

              <div className="pt-3 text-center">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors font-medium"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Back to Portal Sign In
                </Link>
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-[11px] text-slate-500">
          Strict tenant boundary enforced • Vidyasagar State University (VSB Campus)
        </div>
      </div>
    </div>
  );
}
