"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AIExplainability, AISource } from "@campusos/types";
import {
  ChevronDown,
  ChevronUp,
  Database,
  Filter,
  Calculator,
  Calendar,
  ShieldCheck,
  ExternalLink,
  CheckCircle,
} from "lucide-react";

interface ExplainabilityViewProps {
  explainability?: AIExplainability;
  sources?: AISource[];
}

export function ExplainabilityView({ explainability, sources }: ExplainabilityViewProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!explainability && (!sources || sources.length === 0)) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-left text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors py-1 group"
      >
        <span className="flex items-center gap-1.5 font-semibold text-slate-700 group-hover:text-blue-600">
          <Database className="w-3.5 h-3.5 text-blue-500" />
          How this insight was derived & Sources
        </span>
        <span className="flex items-center gap-1 text-slate-500 text-[11px]">
          {isOpen ? "Hide details" : "View data provenance"}
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </span>
      </button>

      {isOpen && (
        <div className="mt-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-3 text-xs text-slate-700 animate-in fade-in duration-200">
          {explainability && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              <div className="space-y-1">
                <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <Database className="w-3 h-3 text-slate-400" /> Data Sources
                </span>
                <div className="flex flex-wrap gap-1">
                  {explainability.dataSources.map((ds, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-800 font-mono text-[11px]"
                    >
                      {ds}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <Filter className="w-3 h-3 text-slate-400" /> Filters Applied
                </span>
                <div className="flex flex-wrap gap-1">
                  {explainability.filtersApplied.map((f, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-800 text-[11px]"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <Calendar className="w-3 h-3 text-slate-400" /> Time Period
                </span>
                <p className="font-medium text-slate-800">{explainability.timePeriod}</p>
              </div>

              <div className="space-y-1">
                <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <Calculator className="w-3 h-3 text-slate-400" /> Calculation Used
                </span>
                <p className="font-mono text-slate-800 text-[11px] bg-white p-1 rounded border border-slate-200">
                  {explainability.calculationUsed}
                </p>
              </div>

              {explainability.threshold && (
                <div className="space-y-1">
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                    <ShieldCheck className="w-3 h-3 text-slate-400" /> Policy Threshold
                  </span>
                  <p className="font-medium text-amber-700">{explainability.threshold}</p>
                </div>
              )}

              <div className="space-y-1">
                <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <CheckCircle className="w-3 h-3 text-emerald-500" /> Computed Result
                </span>
                <p className="font-semibold text-slate-900">{explainability.result}</p>
              </div>
            </div>
          )}

          {sources && sources.length > 0 && (
            <div className="pt-2 border-t border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
                Connected Contextual Systems
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {sources.map((src, idx) => (
                  <Link
                    key={idx}
                    href={src.href}
                    className="flex items-center justify-between p-2 rounded bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-300 transition-colors group"
                  >
                    <div className="truncate pr-2">
                      <p className="font-medium text-slate-800 group-hover:text-blue-700 truncate">
                        {src.name}
                      </p>
                      <p className="text-[11px] text-slate-500 truncate">{src.description}</p>
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 shrink-0" />
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
