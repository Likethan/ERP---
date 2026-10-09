import { ApiResponse } from "@campusos/types";
import {
  Insight,
  InsightPriority,
  InsightStatus,
  IntelligenceDomain,
} from "@campusos/types";
import { MOCK_INSIGHTS } from "@/mocks/intelligence-dataset.mock";

class AiInsightsService {
  private insights: Insight[] = [...MOCK_INSIGHTS];

  async listInsights(filters?: {
    domain?: string;
    priority?: string;
    status?: string;
    search?: string;
    isSaved?: boolean;
  }): Promise<ApiResponse<Insight[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let result = [...this.insights];

    if (filters?.domain && filters.domain !== "ALL") {
      result = result.filter((i) => i.domain === filters.domain);
    }
    if (filters?.priority && filters.priority !== "ALL") {
      result = result.filter((i) => i.priority === filters.priority);
    }
    if (filters?.status && filters.status !== "ALL") {
      result = result.filter((i) => i.status === filters.status);
    }
    if (filters?.isSaved !== undefined) {
      result = result.filter((i) => Boolean(i.isSaved) === filters.isSaved);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          i.summary.toLowerCase().includes(q) ||
          i.recommendedAction.toLowerCase().includes(q)
      );
    }

    return { success: true, data: result };
  }

  async getInsightById(id: string): Promise<ApiResponse<Insight | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const insight = this.insights.find((i) => i.id === id) || null;
    return { success: Boolean(insight), data: insight };
  }

  async toggleSaveInsight(id: string): Promise<ApiResponse<Insight | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const insight = this.insights.find((i) => i.id === id);
    if (!insight) return { success: false, data: null };

    insight.isSaved = !insight.isSaved;
    return { success: true, data: insight };
  }

  async updateInsightStatus(
    id: string,
    status: InsightStatus,
    actor = "User"
  ): Promise<ApiResponse<Insight | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const insight = this.insights.find((i) => i.id === id);
    if (!insight) return { success: false, data: null };

    insight.status = status;
    insight.activityTimeline = insight.activityTimeline || [];
    insight.activityTimeline.push({
      action: `Status changed to ${status}`,
      actor,
      timestamp: new Date().toISOString(),
    });

    return { success: true, data: insight };
  }

  async dismissInsight(id: string, actor = "User"): Promise<ApiResponse<Insight | null>> {
    return this.updateInsightStatus(id, InsightStatus.DISMISSED, actor);
  }

  async markInsightReviewed(id: string, actor = "User"): Promise<ApiResponse<Insight | null>> {
    return this.updateInsightStatus(id, InsightStatus.REVIEWED, actor);
  }

  async markInsightActioned(id: string, actor = "User"): Promise<ApiResponse<Insight | null>> {
    return this.updateInsightStatus(id, InsightStatus.ACTIONED, actor);
  }
}

export const aiInsightsService = new AiInsightsService();
