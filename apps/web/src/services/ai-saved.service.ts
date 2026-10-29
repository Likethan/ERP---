import { ApiResponse } from "@campusos/types";
import { SavedInsight, IntelligenceDomain } from "@campusos/types";
import { MOCK_SAVED_INSIGHTS } from "@/mocks/intelligence-dataset.mock";

class AiSavedService {
  private saved: SavedInsight[] = [...MOCK_SAVED_INSIGHTS];

  async listSavedInsights(filters?: {
    domain?: string;
    type?: string;
    search?: string;
  }): Promise<ApiResponse<SavedInsight[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let result = [...this.saved];

    if (filters?.domain && filters.domain !== "ALL") {
      result = result.filter((s) => s.domain === filters.domain);
    }
    if (filters?.type && filters.type !== "ALL") {
      result = result.filter((s) => s.type === filters.type);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (s) =>
          s.title.toLowerCase().includes(q) ||
          s.contentSnippet.toLowerCase().includes(q),
      );
    }

    return { success: true, data: result };
  }

  async saveItem(payload: {
    title: string;
    type: "AI_RESPONSE" | "INSIGHT" | "ANALYTICS_VIEW" | "REPORT";
    domain: IntelligenceDomain;
    ownerName: string;
    ownerRole: string;
    contentSnippet: string;
    href: string;
  }): Promise<ApiResponse<SavedInsight>> {
    await new Promise((r) => setTimeout(r, 50));
    const newItem: SavedInsight = {
      id: `saved-${Date.now().toString(36)}`,
      title: payload.title,
      type: payload.type,
      domain: payload.domain,
      savedAt: new Date().toISOString(),
      ownerName: payload.ownerName,
      ownerRole: payload.ownerRole,
      lastAccessedAt: new Date().toISOString(),
      contentSnippet: payload.contentSnippet,
      href: payload.href,
    };

    this.saved.unshift(newItem);
    return { success: true, data: newItem };
  }

  async removeSavedInsight(id: string): Promise<ApiResponse<boolean>> {
    await new Promise((r) => setTimeout(r, 40));
    const idx = this.saved.findIndex((s) => s.id === id);
    if (idx === -1) return { success: false, data: false };

    this.saved.splice(idx, 1);
    return { success: true, data: true };
  }
}

export const aiSavedService = new AiSavedService();
