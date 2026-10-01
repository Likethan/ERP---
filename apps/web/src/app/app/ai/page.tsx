"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Bot,
  Send,
  Sparkles,
  Trash2,
  Copy,
  Check,
  ArrowRight,
  Shield,
  Database,
  User,
  HelpCircle,
  Clock,
  Layers,
  FileText,
  Building,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { aiService, AiChatMessage } from "@/services/ai.service";

export default function AiAssistantPage() {
  const { toast } = useToast();
  const [messages, setMessages] = useState<AiChatMessage[]>([
    {
      id: "ai-msg-init",
      sender: "assistant",
      content:
        "Greetings! I am the **CampusOS Enterprise Intelligence Assistant**. I have verified cross-domain access to Student Dossiers, Attendance Registers, Examination Records, Financial Accounts, and Placement Portfolios under your assigned Role-Based Access Control privileges.\n\nHow may I assist your administrative or academic workflow today?",
      timestamp: "Just now",
      suggestedActions: [
        { label: "Campus Intelligence", href: "/app/intelligence" },
        { label: "Today's Attendance", href: "/app/attendance" },
      ],
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState("SUPER_ADMIN");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || input).trim();
    if (!textToSend || loading) return;

    const userMessage: AiChatMessage = {
      id: `usr-msg-${Date.now()}`,
      sender: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await aiService.sendMessage(textToSend, {
        role: selectedRole,
        userName: "Administrator",
        department: "Computer Science & Engineering",
      });

      if (response.success && response.data) {
        setMessages((prev) => [...prev, response.data]);
      }
    } catch {
      toast({
        title: "Assistant Communication Error",
        description: "Unable to reach the CampusOS Reasoning Engine. Please try again.",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
    toast({
      title: "Copied to Clipboard",
      description: "Response text copied successfully.",
      variant: "info",
    });
  };

  const handleClear = () => {
    setMessages([
      {
        id: "ai-msg-init",
        sender: "assistant",
        content:
          "Conversation cleared. How may I assist your institutional workflow today?",
        timestamp: "Just now",
      },
    ]);
    toast({
      title: "Conversation Cleared",
      description: "Assistant session context has been reset.",
      variant: "info",
    });
  };

  const presets = aiService.getPresetPrompts(selectedRole);

  return (
    <div className="space-y-6 pb-12">
      <Breadcrumbs
        customSegments={[
          { label: "CampusOS AI Assistant" },
        ]}
      />

      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-indigo-400">
              <Bot className="h-4 w-4" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              CampusOS AI Assistant
            </h1>
            <Badge variant="outline" className="border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs">
              Context-Aware RAG
            </Badge>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Natural-language queries over academic records, attendance telemetry, fee ledgers, and placement funnels.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleClear}
            className="border-slate-800 bg-slate-900/60 text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <Trash2 className="mr-2 h-3.5 w-3.5 text-slate-400" />
            Clear Session
          </Button>

          <Link href="/app/intelligence">
            <Button
              variant="outline"
              size="sm"
              className="border-slate-800 bg-slate-900/60 text-slate-300 hover:bg-slate-800 hover:text-white"
            >
              <Sparkles className="mr-2 h-3.5 w-3.5 text-yellow-400" />
              Live Telemetry
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left / Center: Chat Stream & Input (8 Cols) */}
        <div className="flex flex-col h-[680px] rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm lg:col-span-8 overflow-hidden shadow-lg">
          {/* Top Bar of Chat */}
          <div className="flex items-center justify-between border-b border-slate-800/80 px-4 py-3 bg-slate-950/40">
            <div className="flex items-center gap-2 text-xs">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-semibold text-white">Reasoning Agent</span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-400 font-mono">Scope: {selectedRole}</span>
            </div>
            <span className="text-[11px] text-slate-500 font-mono">Academic Term 2026-27</span>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((m) => {
              const isAssistant = m.sender === "assistant";
              return (
                <div
                  key={m.id}
                  className={`flex gap-3 ${isAssistant ? "justify-start" : "justify-end"}`}
                >
                  {isAssistant && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-indigo-500/30 bg-indigo-950/60 text-indigo-400 mt-0.5">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-xl p-4 text-xs leading-relaxed space-y-2 shadow-sm ${
                      isAssistant
                        ? "border border-slate-800 bg-slate-950/80 text-slate-200"
                        : "bg-indigo-600 text-white font-medium ml-auto"
                    }`}
                  >
                    <div className="whitespace-pre-wrap font-sans">
                      {m.content}
                    </div>

                    {isAssistant && m.suggestedActions && m.suggestedActions.length > 0 && (
                      <div className="pt-2 mt-2 border-t border-slate-800/80 flex flex-wrap gap-2">
                        {m.suggestedActions.map((act, i) => (
                          <Link key={i} href={act.href}>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-6 text-[11px] px-2.5 border-slate-700 bg-slate-900 text-indigo-300 hover:bg-slate-800 hover:text-white"
                            >
                              {act.label}
                              <ArrowRight className="ml-1 h-3 w-3" />
                            </Button>
                          </Link>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-1 text-[10px] text-slate-500">
                      <span>{m.timestamp}</span>
                      {isAssistant && (
                        <button
                          onClick={() => handleCopy(m.id, m.content)}
                          className="hover:text-slate-300 flex items-center gap-1 transition-colors"
                        >
                          {copiedId === m.id ? (
                            <>
                              <Check className="h-3 w-3 text-emerald-400" />
                              <span className="text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {!isAssistant && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-indigo-400/40 bg-indigo-500/20 text-indigo-300 mt-0.5">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-indigo-500/30 bg-indigo-950/60 text-indigo-400 mt-0.5">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-950/80 px-4 py-3 text-xs text-slate-400 flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
                  Reasoning over institutional knowledge graph...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick preset query pills above input */}
          <div className="px-4 py-2 border-t border-slate-800/60 bg-slate-950/30 flex items-center gap-2 overflow-x-auto no-scrollbar">
            <span className="text-[10px] font-semibold uppercase text-slate-500 shrink-0">
              Suggestions:
            </span>
            {presets.slice(0, 3).map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                disabled={loading}
                className="shrink-0 text-[11px] rounded-full border border-slate-800 bg-slate-900/80 px-3 py-1 text-slate-300 hover:border-indigo-500/50 hover:bg-indigo-950/20 hover:text-white transition-all text-left truncate max-w-[280px]"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="p-3 border-t border-slate-800 bg-slate-950/60">
            <div className="relative flex items-center">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about attendance trends, pending CIA marks, student fees, or placement statistics..."
                rows={1}
                className="w-full resize-none rounded-xl border border-slate-800 bg-slate-900/90 pl-4 pr-12 py-3 text-xs text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              />
              <Button
                size="sm"
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="absolute right-2 h-7 w-7 p-0 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-sm"
              >
                <Send className="h-3.5 w-3.5" />
              </Button>
            </div>
            <div className="mt-1.5 flex items-center justify-between px-1 text-[10px] text-slate-500">
              <span>Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for new line</span>
              <span className="flex items-center gap-1">
                <Shield className="h-3 w-3 text-emerald-400" />
                Audited &amp; PBAC Enforced
              </span>
            </div>
          </div>
        </div>

        {/* Right Sidebar: Context, Governance & Role Presets (4 Cols) */}
        <div className="space-y-4 lg:col-span-4">
          {/* Persona Scope Selector */}
          <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <CardHeader className="pb-3 border-b border-slate-800/80">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <User className="h-3.5 w-3.5 text-indigo-400" />
                Active Persona Persona Scope
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              <p className="text-xs text-slate-400 leading-relaxed">
                CampusOS AI enforces contextual privacy. Change scope to preview persona-tailored responses:
              </p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { role: "SUPER_ADMIN", label: "Executive Admin" },
                  { role: "HOD", label: "Head of Dept" },
                  { role: "FACULTY", label: "Faculty Member" },
                  { role: "STUDENT", label: "Enrolled Student" },
                  { role: "ACCOUNTS", label: "Finance Officer" },
                ].map((item) => (
                  <button
                    key={item.role}
                    onClick={() => setSelectedRole(item.role)}
                    className={`rounded-lg border px-2.5 py-2 text-left text-xs font-medium transition-all ${
                      selectedRole === item.role
                        ? "border-indigo-500 bg-indigo-600/20 text-indigo-300 shadow-sm"
                        : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-white"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Connected Data Sources */}
          <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <CardHeader className="pb-3 border-b border-slate-800/80">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Database className="h-3.5 w-3.5 text-emerald-400" />
                Connected Institutional Graph
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-2.5 text-xs">
              <div className="flex items-center justify-between text-slate-300">
                <span className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Student Dossiers &amp; Curricula
                </span>
                <span className="font-mono text-[11px] text-slate-500">2,280 Records</span>
              </div>
              <div className="flex items-center justify-between text-slate-300">
                <span className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Attendance Registry
                </span>
                <span className="font-mono text-[11px] text-slate-500">Live (87.6%)</span>
              </div>
              <div className="flex items-center justify-between text-slate-300">
                <span className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Continuous Evaluation (CIE)
                </span>
                <span className="font-mono text-[11px] text-slate-500">CIA-1 Active</span>
              </div>
              <div className="flex items-center justify-between text-slate-300">
                <span className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Fee Ledgers &amp; Invoices
                </span>
                <span className="font-mono text-[11px] text-slate-500">₹31.2 Cr Synced</span>
              </div>
              <div className="flex items-center justify-between text-slate-300">
                <span className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Campus Housing &amp; Transport
                </span>
                <span className="font-mono text-[11px] text-slate-500">94.2% Occupancy</span>
              </div>
            </CardContent>
          </Card>

          {/* Governance & Privacy Notice */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4 space-y-2 text-xs text-slate-400">
            <div className="flex items-center gap-2 text-white font-medium">
              <Shield className="h-4 w-4 text-indigo-400" />
              Institutional Privacy &amp; Governance
            </div>
            <p className="leading-relaxed text-[11px]">
              Every query is cryptographically attributed to the logged-in session. Responses only surface verified data from institutionally authenticated tables; generative speculation is strictly prohibited.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
