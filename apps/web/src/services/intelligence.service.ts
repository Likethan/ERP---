import { ApiResponse, AIResponse, AITool } from "@campusos/types";
import { apiFetch } from "@/lib/api-client";
import {
  CampusMetricCard,
  OperationalAlertItem,
  DepartmentKpiItem,
  CohortDistributionItem,
  RiskRadarSummary,
  MOCK_CAMPUS_METRICS,
  MOCK_OPERATIONAL_ALERTS,
  MOCK_DEPARTMENT_KPIS,
  MOCK_COHORT_DATA,
  MOCK_RISK_RADAR,
} from "@/mocks/intelligence.mock";
import {
  IntelligenceOverviewSummary,
  CampusHealthMetric,
  DepartmentHealthSummary,
  StudentIntelligenceProfile,
} from "@campusos/types";
import {
  MOCK_CAMPUS_HEALTH_METRICS,
  MOCK_DEPARTMENT_HEALTH,
  MOCK_STUDENT_INTELLIGENCE,
  MOCK_INSIGHTS,
  MOCK_ALERTS,
} from "@/mocks/intelligence-dataset.mock";
import { calculateCampusHealth } from "./intelligence-calculator";

class IntelligenceService {
  // Legacy compatibility methods
  async getMetrics(): Promise<ApiResponse<CampusMetricCard[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: MOCK_CAMPUS_METRICS };
  }

  async getAlerts(): Promise<ApiResponse<OperationalAlertItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: MOCK_OPERATIONAL_ALERTS };
  }

  async getDepartmentKpis(): Promise<ApiResponse<DepartmentKpiItem[]>> {
    await new Promise((r) => setTimeout(r, 50));
    return { success: true, data: MOCK_DEPARTMENT_KPIS };
  }

  async getCohortData(): Promise<ApiResponse<CohortDistributionItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: MOCK_COHORT_DATA };
  }

  async getRiskRadar(): Promise<ApiResponse<RiskRadarSummary>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: MOCK_RISK_RADAR };
  }

  // ========================================================================
  // Unified Enterprise Intelligence Telemetry & Backend Integration
  // ========================================================================

  async getOverviewSummary(): Promise<
    ApiResponse<IntelligenceOverviewSummary>
  > {
    try {
      const res = await apiFetch<IntelligenceOverviewSummary>(
        "/api/v1/intelligence/overview",
      );
      if (res && res.success && res.data) {
        return res;
      }
    } catch {
      // Graceful fallback to rich mock telemetry during offline/development
    }

    const activeInsightsCount = MOCK_INSIGHTS.filter(
      (i) => i.status !== "DISMISSED",
    ).length;
    const criticalAlertsCount = MOCK_ALERTS.filter(
      (a) => a.severity === "CRITICAL" && a.status === "OPEN",
    ).length;

    const summary: IntelligenceOverviewSummary = {
      activeInsights: activeInsightsCount,
      criticalAlerts: criticalAlertsCount,
      studentsRequiringAttention: 18,
      attendanceRiskCases: 18,
      academicRiskCases: 6,
      financeRiskCases: 36,
      placementOpportunities: 3,
      infrastructureIssues: 3,
      totalQueriesRun: 1480,
      averageQueryDurationMs: 410,
      domainSummaries: {
        Academics: {
          healthScore: 92,
          status: "EXCELLENT",
          summary:
            "92.4% Course Completion; CIA-1 schedules finalized across 42 subject offerings.",
          activeAlerts: 1,
          primaryMetric: "92.4% Pass Rate",
        },
        Attendance: {
          healthScore: 84,
          status: "GOOD",
          summary:
            "86.8% Consolidated Presence; 18 students flagged for examination eligibility review.",
          activeAlerts: 2,
          primaryMetric: "86.8% Average Attendance",
        },
        Examinations: {
          healthScore: 88,
          status: "GOOD",
          summary:
            "42 CIA exams scheduled in Auditorium Hall A; 2 subject marks rosters pending.",
          activeAlerts: 1,
          primaryMetric: "94% Evaluation SLA",
        },
        Finance: {
          healthScore: 86,
          status: "GOOD",
          summary:
            "₹31.2 Cr collected (92.4%); ₹42.8 Lakhs overdue past 30 days across 36 invoices.",
          activeAlerts: 1,
          primaryMetric: "92.4% Fee Realization",
        },
        Placement: {
          healthScore: 94,
          status: "EXCELLENT",
          summary:
            "84.2% Placement Rate; 290 candidate offers released; average package ₹12.4 LPA.",
          activeAlerts: 0,
          primaryMetric: "84.2% Conversion",
        },
        Campus: {
          healthScore: 89,
          status: "GOOD",
          summary:
            "4 major technical symposiums successfully conducted; 78% active club engagement.",
          activeAlerts: 0,
          primaryMetric: "78% Student Engagement",
        },
        Infrastructure: {
          healthScore: 87,
          status: "GOOD",
          summary:
            "Residential halls at 94.2% capacity (32 beds vacant); maintenance turnaround 3.4 hrs.",
          activeAlerts: 1,
          primaryMetric: "94.2% Hostel Occupancy",
        },
        Documents: {
          healthScore: 90,
          status: "EXCELLENT",
          summary:
            "91.8% Record Verification rate; 4 category certificates expiring within 30 days.",
          activeAlerts: 1,
          primaryMetric: "91.8% Compliance",
        },
      },
    };

    return { success: true, data: summary };
  }

  async getCampusHealthMetrics(): Promise<ApiResponse<CampusHealthMetric[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: [...MOCK_CAMPUS_HEALTH_METRICS] };
  }

  async getOverallCampusHealth(): Promise<
    ApiResponse<{
      overallScore: number;
      status: "EXCELLENT" | "GOOD" | "ATTENTION" | "CRITICAL";
      criticalAlertCount: number;
    }>
  > {
    await new Promise((r) => setTimeout(r, 30));
    const result = calculateCampusHealth(MOCK_CAMPUS_HEALTH_METRICS);
    return { success: true, data: result };
  }

  async getDepartmentHealth(
    deptId?: string,
  ): Promise<ApiResponse<DepartmentHealthSummary[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let list = [...MOCK_DEPARTMENT_HEALTH];
    if (deptId) {
      list = list.filter((d) => d.departmentId === deptId);
    }
    return { success: true, data: list };
  }

  async getStudentIntelligenceProfile(
    studentId: string,
  ): Promise<ApiResponse<StudentIntelligenceProfile | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const profile = MOCK_STUDENT_INTELLIGENCE[studentId] || null;
    return { success: Boolean(profile), data: profile };
  }

  // ========================================================================
  // Production Intelligence Engine Backend API Integration
  // ========================================================================

  async query(payload: {
    query: string;
    conversationId?: string;
    context?: {
      type?: string;
      id?: string;
      department?: string;
      program?: string;
      academicYear?: string;
      semester?: string;
      studentId?: string;
    };
  }): Promise<ApiResponse<AIResponse>> {
    return apiFetch<AIResponse>("/api/v1/intelligence/query", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async listConversations(): Promise<ApiResponse<any[]>> {
    return apiFetch<any[]>("/api/v1/intelligence/conversations");
  }

  async getConversationMessages(id: string): Promise<ApiResponse<any[]>> {
    return apiFetch<any[]>(`/api/v1/intelligence/conversations/${id}/messages`);
  }

  async listInsights(
    domain?: string,
    status?: string,
  ): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams();
    if (domain) params.set("domain", domain);
    if (status) params.set("status", status);
    const queryStr = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<any[]>(`/api/v1/intelligence/insights${queryStr}`);
  }

  async listAlerts(
    domain?: string,
    status?: string,
    severity?: string,
  ): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams();
    if (domain) params.set("domain", domain);
    if (status) params.set("status", status);
    if (severity) params.set("severity", severity);
    const queryStr = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<any[]>(`/api/v1/intelligence/alerts${queryStr}`);
  }

  async executeAnalyticsQuery(payload: {
    domain: string;
    metric: string;
    dimension: string;
    timeRange?: string;
    filters?: Record<string, any>;
  }): Promise<ApiResponse<any>> {
    return apiFetch<any>("/api/v1/intelligence/analytics/query", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async listTools(): Promise<ApiResponse<AITool[]>> {
    return apiFetch<AITool[]>("/api/v1/intelligence/tools");
  }

  async listActivity(): Promise<ApiResponse<any[]>> {
    return apiFetch<any[]>("/api/v1/intelligence/activity");
  }

  async listSavedInsights(): Promise<ApiResponse<any[]>> {
    return apiFetch<any[]>("/api/v1/intelligence/saved");
  }
}

export const intelligenceService = new IntelligenceService();
