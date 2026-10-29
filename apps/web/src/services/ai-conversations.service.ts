import { ApiResponse } from "@campusos/types";
import {
  AIConversation,
  AIMessage,
  AIMessageRole,
  AIMessageStatus,
  IntelligenceDomain,
} from "@campusos/types";
import {
  MOCK_AI_CONVERSATIONS,
  MOCK_SEED_MESSAGES,
} from "@/mocks/intelligence-dataset.mock";

class AiConversationsService {
  private conversations: AIConversation[] = [...MOCK_AI_CONVERSATIONS];
  private messages: Record<string, AIMessage[]> = { ...MOCK_SEED_MESSAGES };

  async listConversations(filters?: {
    domain?: string;
    isPinned?: boolean;
    isArchived?: boolean;
    search?: string;
  }): Promise<ApiResponse<AIConversation[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let result = [...this.conversations];

    if (filters?.domain && filters.domain !== "ALL") {
      result = result.filter((c) => c.domain === filters.domain);
    }
    if (filters?.isPinned !== undefined) {
      result = result.filter((c) => c.isPinned === filters.isPinned);
    }
    if (filters?.isArchived !== undefined) {
      result = result.filter((c) => c.isArchived === filters.isArchived);
    } else {
      // By default exclude archived unless specifically requested
      result = result.filter((c) => !c.isArchived);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          c.lastMessageSnippet.toLowerCase().includes(q),
      );
    }

    // Sort pinned first, then by updatedAt desc
    result.sort((a, b) => {
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    });

    return { success: true, data: result };
  }

  async getConversation(
    id: string,
  ): Promise<ApiResponse<AIConversation | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const conv = this.conversations.find((c) => c.id === id) || null;
    return { success: Boolean(conv), data: conv };
  }

  async createConversation(payload: {
    title?: string;
    domain?: IntelligenceDomain;
    firstMessage?: string;
  }): Promise<ApiResponse<AIConversation>> {
    await new Promise((r) => setTimeout(r, 60));
    const id = `conv-${Date.now().toString(36)}`;
    const newConv: AIConversation = {
      id,
      title: payload.title || "New Campus Intelligence Query",
      domain: payload.domain || IntelligenceDomain.ALL,
      isPinned: false,
      isArchived: false,
      isSaved: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messageCount: payload.firstMessage ? 1 : 0,
      lastMessageSnippet: payload.firstMessage || "Conversation started",
    };

    this.conversations.unshift(newConv);
    this.messages[id] = [];

    if (payload.firstMessage) {
      this.messages[id].push({
        id: `msg-${Date.now().toString(36)}`,
        conversationId: id,
        role: AIMessageRole.USER,
        status: AIMessageStatus.COMPLETED,
        content: payload.firstMessage,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      });
    }

    return { success: true, data: newConv };
  }

  async renameConversation(
    id: string,
    newTitle: string,
  ): Promise<ApiResponse<AIConversation | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const conv = this.conversations.find((c) => c.id === id);
    if (!conv) return { success: false, data: null };

    conv.title = newTitle.trim();
    conv.updatedAt = new Date().toISOString();
    return { success: true, data: conv };
  }

  async togglePinConversation(
    id: string,
  ): Promise<ApiResponse<AIConversation | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const conv = this.conversations.find((c) => c.id === id);
    if (!conv) return { success: false, data: null };

    conv.isPinned = !conv.isPinned;
    conv.updatedAt = new Date().toISOString();
    return { success: true, data: conv };
  }

  async toggleSaveConversation(
    id: string,
  ): Promise<ApiResponse<AIConversation | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const conv = this.conversations.find((c) => c.id === id);
    if (!conv) return { success: false, data: null };

    conv.isSaved = !conv.isSaved;
    conv.updatedAt = new Date().toISOString();
    return { success: true, data: conv };
  }

  async archiveConversation(
    id: string,
  ): Promise<ApiResponse<AIConversation | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const conv = this.conversations.find((c) => c.id === id);
    if (!conv) return { success: false, data: null };

    conv.isArchived = true;
    conv.updatedAt = new Date().toISOString();
    return { success: true, data: conv };
  }

  async deleteConversation(id: string): Promise<ApiResponse<boolean>> {
    await new Promise((r) => setTimeout(r, 50));
    const idx = this.conversations.findIndex((c) => c.id === id);
    if (idx === -1) return { success: false, data: false };

    this.conversations.splice(idx, 1);
    delete this.messages[id];
    return { success: true, data: true };
  }

  async getMessages(conversationId: string): Promise<ApiResponse<AIMessage[]>> {
    await new Promise((r) => setTimeout(r, 40));
    const list = this.messages[conversationId] || [];
    return { success: true, data: [...list] };
  }

  async appendMessage(
    conversationId: string,
    message: AIMessage,
  ): Promise<ApiResponse<AIMessage>> {
    if (!this.messages[conversationId]) {
      this.messages[conversationId] = [];
    }
    this.messages[conversationId].push(message);

    const conv = this.conversations.find((c) => c.id === conversationId);
    if (conv) {
      conv.messageCount = this.messages[conversationId].length;
      conv.lastMessageSnippet = message.content.slice(0, 80);
      conv.updatedAt = new Date().toISOString();
    }

    return { success: true, data: message };
  }
}

export const aiConversationsService = new AiConversationsService();
