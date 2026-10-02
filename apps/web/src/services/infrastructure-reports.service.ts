/**
 * CampusOS Infrastructure Reports Service
 * API Contract:
 * GET  /api/v1/infrastructure/reports
 */

import { ApiResponse, InfrastructureReportData } from "@campusos/types";
import { MOCK_INFRASTRUCTURE_REPORTS } from "@/mocks/infrastructure.mock";

class InfrastructureReportsService {
  async getInfrastructureReports(filters?: {
    campusId?: string;
    hostelId?: string;
    routeId?: string;
    facilityId?: string;
    status?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<ApiResponse<InfrastructureReportData>> {
    await new Promise((r) => setTimeout(r, 60));
    // Return structured reports data
    return {
      success: true,
      data: MOCK_INFRASTRUCTURE_REPORTS,
    };
  }
}

export const infrastructureReportsService = new InfrastructureReportsService();
