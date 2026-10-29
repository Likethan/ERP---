import {
  ApiResponse,
  CertificateTemplate,
  CertificateTemplateStatus,
  CertificateType,
} from "@campusos/types";
import { MOCK_CERTIFICATE_TEMPLATES } from "@/mocks/documents.mock";

class CertificateTemplatesService {
  private templates: CertificateTemplate[] = [...MOCK_CERTIFICATE_TEMPLATES];

  async listTemplates(
    audience?: string,
  ): Promise<ApiResponse<CertificateTemplate[]>> {
    await new Promise((r) => setTimeout(r, 30));
    let items = [...this.templates];
    if (audience && audience !== "ALL") {
      items = items.filter(
        (t) =>
          t.applicableAudience.includes("ALL") ||
          t.applicableAudience.includes(audience as any),
      );
    }
    return { success: true, data: items };
  }

  async getTemplateById(
    id: string,
  ): Promise<ApiResponse<CertificateTemplate | null>> {
    await new Promise((r) => setTimeout(r, 20));
    const tmpl = this.templates.find((t) => t.id === id) || null;
    return { success: true, data: tmpl };
  }

  async createTemplate(
    data: Partial<CertificateTemplate>,
  ): Promise<ApiResponse<CertificateTemplate>> {
    await new Promise((r) => setTimeout(r, 60));
    const newTmpl: CertificateTemplate = {
      id: `tmpl-${Date.now()}`,
      templateName: data.templateName || "Custom Institutional Certificate",
      certificateType: data.certificateType || CertificateType.OTHER,
      description: data.description || "",
      applicableAudience: data.applicableAudience || ["STUDENT"],
      status: data.status || CertificateTemplateStatus.ACTIVE,
      version: "1.0",
      fields: data.fields || [
        {
          id: "f-std",
          name: "student_name",
          label: "Student Full Name",
          type: "SYSTEM_VARIABLE",
          required: true,
        },
        {
          id: "f-roll",
          name: "roll_number",
          label: "Roll Number",
          type: "SYSTEM_VARIABLE",
          required: true,
        },
      ],
      createdDate: new Date().toISOString().split("T")[0],
      lastUpdated: new Date().toISOString().split("T")[0],
      usageCount: 0,
      versionHistory: [
        {
          version: "1.0",
          publishedAt: new Date().toISOString(),
          publishedBy: "Dr. Arvind Swaminathan (Registrar)",
          changelog: "Initial production template created",
        },
      ],
      activity: [
        {
          id: `act-${Date.now()}`,
          action: "Template Created",
          performedBy: "Dr. Arvind Swaminathan",
          timestamp: new Date().toISOString(),
          notes: "Published for institutional certificate requests",
        },
      ],
    };

    this.templates.unshift(newTmpl);
    return { success: true, data: newTmpl };
  }

  async updateTemplate(
    id: string,
    data: Partial<CertificateTemplate>,
  ): Promise<ApiResponse<CertificateTemplate>> {
    await new Promise((r) => setTimeout(r, 50));
    const tmpl = this.templates.find((t) => t.id === id);
    if (!tmpl) {
      throw new Error(`Template with ID ${id} not found`);
    }

    Object.assign(tmpl, data);
    tmpl.lastUpdated = new Date().toISOString().split("T")[0];
    if (data.version && data.version !== tmpl.version) {
      tmpl.versionHistory.unshift({
        version: data.version,
        publishedAt: new Date().toISOString(),
        publishedBy: "Dr. Arvind Swaminathan",
        changelog: "Template definition updated",
      });
    }

    return { success: true, data: tmpl };
  }
}

export const certificateTemplatesService = new CertificateTemplatesService();
