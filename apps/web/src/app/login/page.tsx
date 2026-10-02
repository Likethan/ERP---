"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { DEMO_PERSONAS } from "@/mocks/auth.mock";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ShieldCheck, ArrowRight, UserCheck, GraduationCap, Building, Briefcase, Landmark } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, switchPersona } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await login({ email, password });
      router.push("/app/dashboard");
    } catch {
      setErrorMessage("Authentication failed. Please verify credentials or choose a demo persona below.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = (role: string) => {
    switchPersona(role);
    router.push("/app/dashboard");
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case "SUPER_ADMIN":
        return <ShieldCheck className="h-4 w-4 text-emerald-400" />;
      case "HOD":
        return <Building className="h-4 w-4 text-indigo-400" />;
      case "FACULTY":
        return <UserCheck className="h-4 w-4 text-sky-400" />;
      case "STUDENT":
        return <GraduationCap className="h-4 w-4 text-amber-400" />;
      case "ACCOUNTS":
        return <Landmark className="h-4 w-4 text-emerald-400" />;
      case "PLACEMENT_OFFICER":
        return <Briefcase className="h-4 w-4 text-purple-400" />;
      default:
        return <UserCheck className="h-4 w-4 text-slate-400" />;
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12 sm:px-6 lg:px-8 text-slate-100">
      <div className="w-full max-w-md space-y-6">
        {/* Brand & Institution Badge */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Enterprise Security Gateway
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center justify-center gap-2">
            CampusOS
          </h1>
          <p className="text-xs text-slate-400">
            One Campus. One System. One Source of Truth.
          </p>
        </div>

        {/* Credentials Form Box */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl backdrop-blur-sm">
          {errorMessage && (
            <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
              {errorMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Institutional Email
              </label>
              <Input
                type="email"
                placeholder="user@campusos.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Password
              </label>
              <Input
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isSubmitting}
              className="w-full mt-2"
            >
              Sign In to Workspace
            </Button>
          </form>

          {/* Quick Demo Persona Section */}
          <div className="mt-6 pt-6 border-t border-slate-800">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3 text-center">
              Quick Sign In as Demo Persona
            </div>
            <div className="space-y-1.5">
              {DEMO_PERSONAS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleQuickLogin(p.role)}
                  className="w-full flex items-center justify-between p-2.5 rounded-lg border border-slate-800/80 bg-slate-950/60 hover:bg-slate-800 hover:border-slate-700 text-left transition-all cursor-pointer group"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    {getRoleIcon(p.role)}
                    <div className="truncate">
                      <div className="text-xs font-semibold text-white group-hover:text-indigo-300 transition-colors">
                        {p.name}
                      </div>
                      <div className="text-[10px] text-slate-400 truncate">
                        {p.roleTitle}
                      </div>
                    </div>
                  </div>
                  <ArrowRight className="h-3.5 w-3.5 text-slate-600 group-hover:text-white transition-colors shrink-0" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* System Integrity Footer */}
        <div className="text-center text-[11px] text-slate-500">
          Strict tenant boundary enforced • Vidyasagar State University (VSB Campus)
        </div>
      </div>
    </div>
  );
}
