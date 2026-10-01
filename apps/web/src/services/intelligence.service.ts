import { ApiResponse } from "@campusos/types";
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

class IntelligenceService {
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
}

export const intelligenceService = new IntelligenceService();
