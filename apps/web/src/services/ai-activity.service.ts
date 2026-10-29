import { ApiResponse } from "@campusos/types";
import {
  AIActivity,
  AIActivityStatus,
  IntelligenceDomain,
} from "@campusos/types";
import { MOCK_AI_ACTIVITIES } from "@/mocks/intelligence-dataset.mock";

class AiActivityService {
  private activities: AIActivity[] = [...MOCK_AI_ACTIVITIES];

  async listAIActivity(filters?: {
    domain?: string;
    status?: string;
    search?: string;
  }): Promise<ApiResponse<AIActivity[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let result = [...this.activities];

    if (filters?.domain && filters.domain !== "ALL") {
      result = result.filter((a) => a.domain === filters.domain);
    }
    if (filters?.status && filters.status !== "ALL") {
      result = result.filter((a) => a.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (a) =>
          a.query.toLowerCase().includes(q) ||
          a.userName.toLowerCase().includes(q) ||
          a.resultSummary.toLowerCase().includes(q) ||
          a.toolsInvoked.some((t) => t.toLowerCase().includes(q)),
      );
    }

    return { success: true, data: result };
  }

  async getActivityById(id: string): Promise<ApiResponse<AIActivity | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const act = this.activities.find((a) => a.id === id) || null;
    return { success: Boolean(act), data: act };
  }

  async logActivity(payload: {
    userName: string;
    userRole: string;
    query: string;
    domain: IntelligenceDomain;
    toolsInvoked: string[];
    resultSummary: string;
    durationMs: number;
    status: AIActivityStatus;
    dataSources: string[];
    contextSummary?: string;
  }): Promise<ApiResponse<AIActivity>> {
    const newAct: AIActivity = {
      id: `act-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      ...payload,
    };

    this.activities.unshift(newAct);
    return { success: true, data: newAct };
  }
}

export const aiActivityService = new AiActivityService();
