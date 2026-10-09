"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Sparkles,
  Bot,
  Send,
  User,
  Clock,
  Pin,
  Bookmark,
  BookmarkCheck,
  Trash2,
  Edit2,
  Layers,
  ChevronRight,
  Database,
  ExternalLink,
  ShieldCheck,
  Plus,
  RefreshCw,
  Search,
  Check,
  ArrowRight,
  HelpCircle,
  X,
  Sidebar as SidebarIcon,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import {
  aiConversationsService,
  aiAssistantService,
  aiSavedService,
} from "@/services";
import {
  AIConversation,
  AIMessage,
  AIMessageRole,
  AIMessageStatus,
  IntelligenceDomain,
  AISource,
} from "@campusos/types";
import { AIQueryComposer } from "@/components/intelligence/ai-query-composer";
import { StructuredResponseView } from "@/components/intelligence/structured-response-view";
import { ExplainabilityView } from "@/components/intelligence/explainability-drawer";
import { DomainBadge } from "@/components/intelligence/intelligence-badge";

export default function AiAssistantConsolePage() {
  const { toast } = useToast();

  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchConv, setSearchConv] = useState("");
  const [showRightPanel, setShowRightPanel] = useState(true);

  // Rename modal
  const [renameTarget, setRenameTarget] = useState<AIConversation | null>(null);
  const [newTitle, setNewTitle] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load conversations on mount
  useEffect(() => {
    const fetchConversations = async () => {
      const res = await aiConversationsService.listConversations();
      if (res.success && res.data) {
        setConversations(res.data);
        if (res.data.length > 0 && !activeConvId) {
          setActiveConvId(res.data[0].id);
        }
      }
    };
    fetchConversations();
  }, []);

  // Load messages when activeConvId changes
  useEffect(() => {
    if (!activeConvId) {
      setMessages([]);
      return;
    }

    const fetchMessages = async () => {
      const res = await aiConversationsService.getMessages(activeConvId);
      if (res.success && res.data) {
        setMessages(res.data);
      }
    };
    fetchMessages();
  }, [activeConvId]);

  const handleNewChat = async () => {
    const res = await aiConversationsService.createConversation({
      title: "New Campus Query",
      domain: IntelligenceDomain.ALL,
    });
    if (res.success && res.data) {
      setConversations((prev) => [res.data, ...prev]);
      setActiveConvId(res.data.id);
      setMessages([]);
    }
  };

  const handleSendQuery = async (queryText: string, domain: IntelligenceDomain, context?: any) => {
    let currentConvId = activeConvId;

    // Create conversation if none active
    if (!currentConvId) {
      const newConvRes = await aiConversationsService.createConversation({
        title: queryText.slice(0, 35) + (queryText.length > 35 ? "..." : ""),
        domain,
      });
      if (newConvRes.success && newConvRes.data) {
        currentConvId = newConvRes.data.id;
        setActiveConvId(currentConvId);
        setConversations((prev) => [newConvRes.data, ...prev]);
      } else {
        return;
      }
    }

    // Append User Message
    const userMsg: AIMessage = {
      id: `usr-${Date.now().toString(36)}`,
      conversationId: currentConvId,
      role: AIMessageRole.USER,
      status: AIMessageStatus.COMPLETED,
      content: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    await aiConversationsService.appendMessage(currentConvId, userMsg);
    setLoading(true);

    try {
      const response = await aiAssistantService.sendQuery({
        query: queryText,
        domain,
        context: {
          role: "SUPER_ADMIN",
          userName: "Administrator",
          ...context,
        },
        conversationId: currentConvId,
      });

      if (response.success && response.data) {
        const aiMsg: AIMessage = {
          id: response.data.id,
          conversationId: currentConvId,
          role: AIMessageRole.ASSISTANT,
          status: AIMessageStatus.COMPLETED,
          content: response.data.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          blocks: response.data.blocks,
          sources: response.data.sources,
          explainability: response.data.explainability,
          suggestedActions: response.data.suggestedActions,
        };

        setMessages((prev) => [...prev, aiMsg]);
        await aiConversationsService.appendMessage(currentConvId, aiMsg);

        // Update conversation title if generic
        const currentConv = conversations.find((c) => c.id === currentConvId);
        if (currentConv && currentConv.title.startsWith("New Campus")) {
          const generatedTitle = queryText.slice(0, 36) + (queryText.length > 36 ? "..." : "");
          await aiConversationsService.renameConversation(currentConvId, generatedTitle);
          setConversations((prev) =>
            prev.map((c) => (c.id === currentConvId ? { ...c, title: generatedTitle } : c))
          );
        }
      }
    } catch {
      toast({
        title: "Reasoning Engine Error",
        description: "Unable to synthesize cross-domain intelligence answer. Please retry.",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveResponse = async (msg: AIMessage) => {
    const res = await aiSavedService.saveItem({
      title: msg.content.slice(0, 40) + "...",
      type: "AI_RESPONSE",
      domain: IntelligenceDomain.ALL,
      ownerName: "Administrator",
      ownerRole: "SUPER_ADMIN",
      contentSnippet: msg.content.slice(0, 100),
      href: `/app/intelligence/assistant?conv=${activeConvId}`,
    });

    if (res.success) {
      toast({
        title: "Response Saved",
        description: "Added to your Saved Insights portfolio.",
        variant: "success",
      });
    }
  };

  const handlePin = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const res = await aiConversationsService.togglePinConversation(id);
    if (res.success && res.data) {
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, isPinned: res.data!.isPinned } : c))
      );
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const res = await aiConversationsService.deleteConversation(id);
    if (res.success) {
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConvId === id) {
        const remaining = conversations.filter((c) => c.id !== id);
        setActiveConvId(remaining.length > 0 ? remaining[0].id : null);
      }
      toast({
        title: "Conversation Deleted",
        description: "Conversation history removed.",
        variant: "neutral",
      });
    }
  };

  const handleRenameConfirm = async () => {
    if (!renameTarget || !newTitle.trim()) return;
    const res = await aiConversationsService.renameConversation(renameTarget.id, newTitle);
    if (res.success && res.data) {
      setConversations((prev) =>
        prev.map((c) => (c.id === renameTarget.id ? { ...c, title: newTitle.trim() } : c))
      );
      toast({ title: "Conversation Renamed", variant: "success" });
    }
    setRenameTarget(null);
    setNewTitle("");
  };

  // Find latest active sources for right panel
  const activeSources: AISource[] = [];
  messages.forEach((m) => {
    if (m.sources) {
      m.sources.forEach((s) => {
        if (!activeSources.some((existing) => existing.name === s.name)) {
          activeSources.push(s);
        }
      });
    }
  });

  const activeConversation = conversations.find((c) => c.id === activeConvId);
  const promptPresets = aiAssistantService.getSuggestedPrompts("SUPER_ADMIN");

  const filteredConversations = conversations.filter((c) => {
    if (!searchConv) return true;
    return (
      c.title.toLowerCase().includes(searchConv.toLowerCase()) ||
      c.lastMessageSnippet.toLowerCase().includes(searchConv.toLowerCase())
    );
  });

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] -m-4 sm:-m-6">
      {/* Top Console Bar */}
      <div className="h-14 px-4 sm:px-6 border-b border-slate-200 bg-white flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Breadcrumbs
            items={[
              { label: "Dashboard", href: "/app/dashboard" },
              { label: "Intelligence", href: "/app/intelligence" },
              { label: "AI Assistant" },
            ]}
          />
        </div>

        <div className="flex items-center gap-2">
          {activeConversation && (
            <DomainBadge domain={activeConversation.domain} />
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowRightPanel(!showRightPanel)}
            className="hidden lg:flex items-center gap-1.5 text-xs text-slate-600"
            title="Toggle Context Panel"
          >
            <SidebarIcon className="w-4 h-4" />
            <span className="hidden xl:inline">{showRightPanel ? "Hide Sources" : "Show Sources"}</span>
          </Button>

          <Button
            size="sm"
            onClick={handleNewChat}
            className="gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-3.5 h-3.5" />
            New Chat
          </Button>
        </div>
      </div>

      {/* 3-Panel Composition */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Conversation History */}
        <aside className="w-72 lg:w-80 border-r border-slate-200 bg-slate-50/60 flex flex-col shrink-0 hidden md:flex">
          <div className="p-3 border-b border-slate-200 space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchConv}
                onChange={(e) => setSearchConv(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filteredConversations.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                No conversations found.
              </div>
            ) : (
              filteredConversations.map((conv) => {
                const isActive = conv.id === activeConvId;
                return (
                  <div
                    key={conv.id}
                    onClick={() => setActiveConvId(conv.id)}
                    className={`w-full text-left p-2.5 rounded-xl text-xs transition-all cursor-pointer group relative flex flex-col justify-between ${
                      isActive
                        ? "bg-white shadow-sm border border-blue-200 text-slate-900"
                        : "hover:bg-slate-200/60 text-slate-700 border border-transparent"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <div className="flex items-center gap-1.5 truncate pr-2">
                        {conv.isPinned && (
                          <Pin className="w-3 h-3 text-amber-500 fill-amber-500 shrink-0" />
                        )}
                        <span className={`font-semibold truncate ${isActive ? "text-blue-900" : "text-slate-800"}`}>
                          {conv.title}
                        </span>
                      </div>

                      {/* Hover action menu */}
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => handlePin(conv.id, e)}
                          className="p-1 hover:text-amber-600 rounded"
                          title={conv.isPinned ? "Unpin" : "Pin"}
                        >
                          <Pin className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setRenameTarget(conv);
                            setNewTitle(conv.title);
                          }}
                          className="p-1 hover:text-blue-600 rounded"
                          title="Rename"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => handleDelete(conv.id, e)}
                          className="p-1 hover:text-rose-600 rounded"
                          title="Delete"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-500 line-clamp-1 mb-1">
                      {conv.lastMessageSnippet}
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span>{new Date(conv.updatedAt).toLocaleDateString([], { month: "short", day: "numeric" })}</span>
                      <span className="font-medium text-slate-500">{conv.domain}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </aside>

        {/* Center Panel: Conversation Thread & Empty State */}
        <main className="flex-1 flex flex-col bg-white overflow-hidden">
          {messages.length === 0 ? (
            /* Empty State (Section 6) */
            <div className="flex-1 overflow-y-auto p-6 sm:p-12 flex flex-col items-center justify-center text-center max-w-2xl mx-auto space-y-6">
              <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-sm">
                <Sparkles className="w-7 h-7" />
              </div>

              <div className="space-y-2">
                <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
                  What do you want to understand about your campus?
                </h2>
                <p className="text-sm text-slate-500 max-w-lg mx-auto">
                  Ask questions across academics, attendance, finance, placement, campus operations and more.
                </p>
              </div>

              {/* Clickable prompt suggestions (Section 6) */}
              <div className="w-full space-y-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                  Click a question to begin analysis:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                  {promptPresets.map((p, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendQuery(p.query, p.domain)}
                      className="p-3 rounded-xl border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 transition-all text-xs font-medium text-slate-800 flex items-center justify-between group shadow-sm"
                    >
                      <span className="line-clamp-2 pr-2">{p.query}</span>
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Message Thread */
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
              {messages.map((msg) => {
                const isUser = msg.role === AIMessageRole.USER;
                return (
                  <div
                    key={msg.id}
                    className={`flex gap-3 max-w-3xl ${
                      isUser ? "ml-auto justify-end" : "mr-auto"
                    }`}
                  >
                    {!isUser && (
                      <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                        <Sparkles className="w-4 h-4" />
                      </div>
                    )}

                    <div
                      className={`rounded-2xl p-4 text-sm leading-relaxed ${
                        isUser
                          ? "bg-blue-600 text-white shadow-sm max-w-xl"
                          : "bg-slate-50 border border-slate-200/90 text-slate-800 w-full shadow-sm"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1.5 text-xs">
                        <span className={`font-semibold ${isUser ? "text-blue-100" : "text-slate-900"}`}>
                          {isUser ? "You" : "CampusOS Intelligence"}
                        </span>
                        <div className="flex items-center gap-1.5 text-[11px] opacity-75">
                          <span>{msg.timestamp}</span>
                          {!isUser && (
                            <button
                              type="button"
                              onClick={() => handleSaveResponse(msg)}
                              className="p-1 hover:text-blue-600 rounded"
                              title="Save to Saved Insights"
                            >
                              <Bookmark className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>

                      <p className="whitespace-pre-line leading-relaxed">{msg.content}</p>

                      {/* Structured Response Blocks */}
                      {!isUser && <StructuredResponseView blocks={msg.blocks} />}

                      {/* Explainability & Sources */}
                      {!isUser && (
                        <ExplainabilityView
                          explainability={msg.explainability}
                          sources={msg.sources}
                        />
                      )}

                      {/* Suggested Quick Links */}
                      {!isUser && msg.suggestedActions && (
                        <div className="flex flex-wrap items-center gap-2 pt-2 mt-2 border-t border-slate-200/60">
                          <span className="text-[11px] font-semibold text-slate-400">Quick Links:</span>
                          {msg.suggestedActions.map((act, aIdx) => (
                            <Link key={aIdx} href={act.href}>
                              <span className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium hover:underline">
                                {act.label} <ArrowRight className="w-3 h-3" />
                              </span>
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>

                    {isUser && (
                      <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                        <User className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                );
              })}

              {loading && (
                <div className="flex gap-3 max-w-xl mr-auto animate-pulse">
                  <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div className="rounded-2xl p-4 bg-slate-50 border border-slate-200 text-xs text-slate-500 space-y-2 w-72">
                    <div className="h-4 bg-slate-200 rounded w-3/4" />
                    <div className="h-3 bg-slate-200 rounded w-full" />
                    <div className="h-3 bg-slate-200 rounded w-1/2" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Bottom Query Composer */}
          <AIQueryComposer
            onSend={handleSendQuery}
            loading={loading}
            presetPrompts={promptPresets}
          />
        </main>

        {/* Right Panel: Context & Data Sources */}
        {showRightPanel && (
          <aside className="w-72 lg:w-80 border-l border-slate-200 bg-slate-50/50 p-4 space-y-4 overflow-y-auto hidden lg:block shrink-0">
            <div>
              <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-blue-600" />
                Active Knowledge Context
              </h3>
              <p className="text-[11px] text-slate-500">
                Connected enterprise registers governing current query scope
              </p>
            </div>

            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-2 text-xs">
              <div className="flex items-center justify-between text-slate-600">
                <span className="text-[11px] text-slate-400">Institutional Scope</span>
                <span className="font-semibold text-slate-800">VSB Campus (Full)</span>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span className="text-[11px] text-slate-400">Security Clearance</span>
                <Badge variant="success" className="text-[10px]">SUPER_ADMIN</Badge>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span className="text-[11px] text-slate-400">Active Term</span>
                <span className="font-medium text-slate-800">2026 – 2027</span>
              </div>
            </div>

            {/* Active Sources */}
            <div>
              <span className="text-xs font-semibold text-slate-900 uppercase tracking-wider block mb-2">
                Referenced Subsystems ({activeSources.length})
              </span>
              {activeSources.length === 0 ? (
                <div className="p-4 rounded-xl bg-white border border-slate-200 text-center text-xs text-slate-400">
                  Submit a query to inspect live contextual data sources.
                </div>
              ) : (
                <div className="space-y-1.5">
                  {activeSources.map((s, idx) => (
                    <Link
                      key={idx}
                      href={s.href}
                      className="p-2.5 rounded-lg bg-white border border-slate-200 hover:border-blue-400 transition-colors block text-xs group"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-800 group-hover:text-blue-600 truncate">
                          {s.name}
                        </span>
                        <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-blue-600 shrink-0" />
                      </div>
                      <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">{s.description}</p>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* Safety & Compliance Notice */}
            <div className="p-3 rounded-xl bg-blue-50/60 border border-blue-200 text-[11px] text-blue-900 space-y-1">
              <span className="font-semibold flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                Enterprise Compliance
              </span>
              <p className="text-blue-800/80 leading-relaxed">
                Queries are executed strictly within role-based access boundaries. No sensitive data is shared outside institutional walls.
              </p>
            </div>
          </aside>
        )}
      </div>

      {/* Rename Dialog */}
      <Dialog
        open={Boolean(renameTarget)}
        onOpenChange={(open) => !open && setRenameTarget(null)}
        title="Rename Conversation"
      >
        <div className="space-y-3 pt-2">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm text-slate-800 focus:outline-none focus:border-blue-500"
            placeholder="Conversation title"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setRenameTarget(null)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleRenameConfirm} disabled={!newTitle.trim()}>
              Save Title
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
