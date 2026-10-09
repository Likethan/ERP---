"use client";

import React from "react";
import Link from "next/link";
import {
  AIResponseBlock,
  AIResponseBlockType,
} from "@campusos/types";
import {
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  Calendar,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface StructuredResponseViewProps {
  blocks?: AIResponseBlock[];
}

export function StructuredResponseView({ blocks }: StructuredResponseViewProps) {
  if (!blocks || blocks.length === 0) return null;

  return (
    <div className="space-y-4 my-3">
      {blocks.map((block, idx) => {
        switch (block.type) {
          case AIResponseBlockType.METRIC:
            return (
              <div key={idx} className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {block.metrics?.map((m, mIdx) => (
                  <div
                    key={mIdx}
                    className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex flex-col justify-between"
                  >
                    <p className="text-xs text-slate-500 font-medium truncate">{m.label}</p>
                    <div className="flex items-baseline justify-between mt-1">
                      <span className="text-lg font-bold text-slate-900">{m.value}</span>
                      {m.change && (
                        <span
                          className={`inline-flex items-center gap-0.5 text-[11px] font-semibold ${
                            m.trend === "up"
                              ? "text-emerald-700"
                              : m.trend === "down"
                              ? "text-rose-700"
                              : "text-slate-600"
                          }`}
                        >
                          {m.trend === "up" ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : m.trend === "down" ? (
                            <TrendingDown className="w-3 h-3" />
                          ) : (
                            <Minus className="w-3 h-3" />
                          )}
                          {m.change}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            );

          case AIResponseBlockType.TABLE:
            return (
              <div key={idx} className="rounded-lg border border-slate-200 overflow-hidden bg-white">
                {block.title && (
                  <div className="px-3 py-2 bg-slate-50 border-b border-slate-200 font-semibold text-xs text-slate-800">
                    {block.title}
                  </div>
                )}
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50/80 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                      <tr>
                        {block.table?.headers.map((h, hIdx) => (
                          <th key={hIdx} className="px-3 py-2">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {block.table?.rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-50/50">
                          {row.map((cell, cIdx) => (
                            <td key={cIdx} className="px-3 py-2 text-slate-800">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );

          case AIResponseBlockType.RECOMMENDATION:
          case AIResponseBlockType.LIST:
            return (
              <div key={idx} className="p-3.5 rounded-lg bg-blue-50/60 border border-blue-100">
                {block.title && (
                  <div className="flex items-center gap-1.5 font-semibold text-xs text-blue-900 mb-2">
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                    {block.title}
                  </div>
                )}
                <ul className="space-y-1.5 text-xs text-slate-700">
                  {block.list?.map((item, lIdx) => (
                    <li key={lIdx} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );

          case AIResponseBlockType.WARNING:
            return (
              <div key={idx} className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900">
                <div className="flex items-center gap-1.5 font-semibold text-xs mb-1">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  {block.title || "Operational Notice"}
                </div>
                {block.content && <p className="text-xs text-amber-800">{block.content}</p>}
              </div>
            );

          case AIResponseBlockType.ACTION:
            return (
              <div key={idx} className="flex flex-wrap gap-2 pt-1">
                {block.actions?.map((act, aIdx) => (
                  <Link key={aIdx} href={act.href || "#"}>
                    <Button size="sm" variant={act.variant === "primary" ? "primary" : "outline"} className="gap-1 text-xs">
                      {act.label}
                      <ArrowRight className="w-3 h-3" />
                    </Button>
                  </Link>
                ))}
              </div>
            );

          default:
            return null;
        }
      })}
    </div>
  );
}
