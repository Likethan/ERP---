import { ApiResponse } from "@campusos/types";
import { AITool, AIToolExecution } from "@campusos/types";
import { MOCK_AI_TOOLS } from "@/mocks/intelligence-dataset.mock";

class AiToolsService {
  private tools: AITool[] = [...MOCK_AI_TOOLS];
  private executions: AIToolExecution[] = [];

  async listAITools(filters?: {
    domain?: string;
    permission?: string;
    status?: string;
    search?: string;
  }): Promise<ApiResponse<AITool[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let result = [...this.tools];

    if (filters?.domain && filters.domain !== "ALL") {
      result = result.filter((t) => t.domain === filters.domain);
    }
    if (filters?.status) {
      result = result.filter((t) => t.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (t) =>
          t.name.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q)
      );
    }

    return { success: true, data: result };
  }

  async getAITool(name: string): Promise<ApiResponse<AITool | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const tool = this.tools.find((t) => t.name === name) || null;
    return { success: Boolean(tool), data: tool };
  }

  async logExecution(payload: {
    toolName: string;
    user: string;
    role: string;
    durationMs: number;
    status: "SUCCESS" | "FAILED";
    inputParameters?: Record<string, any>;
    recordsReturned?: number;
  }): Promise<ApiResponse<AIToolExecution>> {
    const execution: AIToolExecution = {
      id: `exec-${Date.now().toString(36)}`,
      toolName: payload.toolName,
      timestamp: new Date().toISOString(),
      user: payload.user,
      role: payload.role,
      durationMs: payload.durationMs,
      status: payload.status,
      inputParameters: payload.inputParameters || {},
      recordsReturned: payload.recordsReturned ?? 1,
    };

    this.executions.unshift(execution);

    // Update tool telemetry
    const tool = this.tools.find((t) => t.name === payload.toolName);
    if (tool) {
      tool.executionCount += 1;
      tool.lastUsed = "Just now";
    }

    return { success: true, data: execution };
  }

  async listExecutions(): Promise<ApiResponse<AIToolExecution[]>> {
    return { success: true, data: [...this.executions] };
  }
}

export const aiToolsService = new AiToolsService();
