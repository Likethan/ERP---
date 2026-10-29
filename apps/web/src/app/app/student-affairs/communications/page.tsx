"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import {
  GrievanceCaseModel,
  CaseCommunicationModel,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  MessageSquare,
  Lock,
  Send,
  Paperclip,
  CheckCircle2,
  ShieldCheck,
  User,
} from "lucide-react";

function CommunicationsContent() {
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams?.get("caseId");

  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(preselectedCaseId || "");
  const [messages, setMessages] = useState<CaseCommunicationModel[]>([]);
  const [messageBody, setMessageBody] = useState("");
  const [isInternalOnly, setIsInternalOnly] = useState(false);
  const [attachmentUrl, setAttachmentUrl] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      const allCases = await studentAffairsService.getCases();
      setCases(allCases);
      if (preselectedCaseId) {
        setSelectedCaseId(preselectedCaseId);
      } else if (allCases.length > 0) {
        setSelectedCaseId(allCases[0].id);
      }
    }
    load();
  }, [preselectedCaseId]);

  useEffect(() => {
    if (!selectedCaseId) return;
    const match = cases.find((c) => c.id === selectedCaseId);
    setMessages(match?.communications || []);
  }, [selectedCaseId, cases]);

  async function handleSendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCaseId || !messageBody) return;

    setLoading(true);
    try {
      const sent = await studentAffairsService.sendConfidentialMessage({
        caseId: selectedCaseId,
        messageBody,
        isInternalOnly,
        attachmentUrl: attachmentUrl || undefined,
      });
      setMessages((prev) => [...prev, sent]);
      setMessageBody("");
      setAttachmentUrl("");
    } catch {
      alert("Error transmitting confidential message.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "Confidential Communications", href: "/app/student-affairs/communications" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <MessageSquare className="h-6 w-6 text-indigo-400" />
          Confidential Case Communications & Clarifications
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Secure, audit-logged message channel for requests for additional information, formal notices, and hearing logistics.
        </p>
      </div>

      <StudentAffairsNav />

      {/* Case Selector */}
      <Card className="p-4 border-slate-800 bg-slate-900/40">
        <label className="block text-xs font-medium text-slate-400 mb-1.5">
          Select Active Case Thread
        </label>
        <select
          value={selectedCaseId}
          onChange={(e) => setSelectedCaseId(e.target.value)}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
        >
          {cases.map((c) => (
            <option key={c.id} value={c.id}>
              {c.case_number} - {c.title} ({c.communications?.length || 0} messages)
            </option>
          ))}
        </select>
      </Card>

      {/* Messages Thread Container */}
      <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4 min-h-[350px] flex flex-col justify-between">
        <div className="space-y-3 overflow-y-auto max-h-[400px]">
          {messages.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs italic">
              No messages recorded in this case thread yet. Use the prompt below to request clarification or schedule a conference.
            </div>
          ) : (
            messages.map((m) => (
              <div
                key={m.id}
                className={`p-3.5 rounded-xl border text-xs space-y-1.5 ${
                  m.is_internal_only
                    ? "border-amber-500/30 bg-amber-950/20 ml-6"
                    : "border-slate-800 bg-slate-950/60"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-indigo-400" />
                    <span className="font-semibold text-white">{m.sender_role}</span>
                    {m.is_internal_only && (
                      <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[9px]">
                        Internal Note
                      </Badge>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {new Date(m.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-slate-300 leading-relaxed">{m.message_body}</p>
                {m.attachment_url && (
                  <div className="pt-1 text-[11px] text-indigo-400 flex items-center gap-1">
                    <Paperclip className="h-3 w-3" />
                    <span>Attached Document</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Input Box */}
        <form onSubmit={handleSendMessage} className="space-y-3 pt-3 border-t border-slate-800/80">
          <textarea
            rows={3}
            placeholder="Type confidential message, request for information, or committee deliberation note..."
            value={messageBody}
            onChange={(e) => setMessageBody(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            required
          />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isInternalOnly}
                  onChange={(e) => setIsInternalOnly(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700"
                />
                <span>Internal Committee Note Only (Hide from student)</span>
              </label>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs gap-1.5"
            >
              <Send className="h-3.5 w-3.5" />
              Transmit Message
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

export default function CommunicationsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading communications...</div>}>
      <CommunicationsContent />
    </Suspense>
  );
}

