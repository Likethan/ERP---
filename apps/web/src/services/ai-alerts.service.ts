import { ApiResponse } from "@campusos/types";
import { Alert, AlertSeverity, AlertStatus } from "@campusos/types";
import { MOCK_ALERTS } from "@/mocks/intelligence-dataset.mock";

class AiAlertsService {
  private alerts: Alert[] = [...MOCK_ALERTS];

  async listAlerts(filters?: {
    domain?: string;
    severity?: string;
    status?: string;
    search?: string;
  }): Promise<ApiResponse<Alert[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let result = [...this.alerts];

    if (filters?.domain && filters.domain !== "ALL") {
      result = result.filter((a) => a.domain === filters.domain);
    }
    if (filters?.severity && filters.severity !== "ALL") {
      result = result.filter((a) => a.severity === filters.severity);
    }
    if (filters?.status && filters.status !== "ALL") {
      result = result.filter((a) => a.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (a) =>
          a.title.toLowerCase().includes(q) ||
          a.reason.toLowerCase().includes(q) ||
          a.sourceDomain.toLowerCase().includes(q),
      );
    }

    return { success: true, data: result };
  }

  async getAlertById(id: string): Promise<ApiResponse<Alert | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const alert = this.alerts.find((a) => a.id === id) || null;
    return { success: Boolean(alert), data: alert };
  }

  async acknowledgeAlert(
    id: string,
    actor: string,
  ): Promise<ApiResponse<Alert | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const alert = this.alerts.find((a) => a.id === id);
    if (!alert) return { success: false, data: null };

    alert.status = AlertStatus.ACKNOWLEDGED;
    alert.acknowledgedAt = new Date().toISOString();
    alert.acknowledgedBy = actor;

    alert.activityTimeline = alert.activityTimeline || [];
    alert.activityTimeline.push({
      action: "Alert Acknowledged",
      actor,
      timestamp: new Date().toISOString(),
      notes: "Assigned for departmental investigation",
    });

    return { success: true, data: alert };
  }

  async resolveAlert(
    id: string,
    actor: string,
    notes = "Action completed",
  ): Promise<ApiResponse<Alert | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const alert = this.alerts.find((a) => a.id === id);
    if (!alert) return { success: false, data: null };

    alert.status = AlertStatus.RESOLVED;
    alert.resolvedAt = new Date().toISOString();
    alert.resolvedBy = actor;

    alert.activityTimeline = alert.activityTimeline || [];
    alert.activityTimeline.push({
      action: "Alert Resolved",
      actor,
      timestamp: new Date().toISOString(),
      notes,
    });

    return { success: true, data: alert };
  }

  async dismissAlert(
    id: string,
    actor: string,
  ): Promise<ApiResponse<Alert | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const alert = this.alerts.find((a) => a.id === id);
    if (!alert) return { success: false, data: null };

    alert.status = AlertStatus.DISMISSED;

    alert.activityTimeline = alert.activityTimeline || [];
    alert.activityTimeline.push({
      action: "Alert Dismissed",
      actor,
      timestamp: new Date().toISOString(),
    });

    return { success: true, data: alert };
  }
}

export const aiAlertsService = new AiAlertsService();
