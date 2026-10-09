import { ApiResponse } from "@campusos/types";
import {
  InstitutionalRecord,
  InstitutionalRecordStatus,
  ConfidentialityLevel,
} from "@campusos/types";
import { MOCK_INSTITUTIONAL_RECORDS } from "@/mocks/documents.mock";

class InstitutionalRecordsService {
  private records: InstitutionalRecord[] = [...MOCK_INSTITUTIONAL_RECORDS];

  async listRecords(filters?: {
    category?: string;
    department?: string;
    confidentiality?: string;
    status?: string;
    search?: string;
  }): Promise<ApiResponse<InstitutionalRecord[]>> {
    await new Promise((r) => setTimeout(r, 30));
    let items = [...this.records];

    if (filters) {
      if (filters.category && filters.category !== "ALL") {
        items = items.filter((rec) => rec.category === filters.category);
      }
      if (filters.department && filters.department !== "ALL") {
        items = items.filter((rec) => rec.ownerDepartment === filters.department);
      }
      if (filters.confidentiality && filters.confidentiality !== "ALL") {
        items = items.filter((rec) => rec.confidentiality === filters.confidentiality);
      }
      if (filters.status && filters.status !== "ALL") {
        items = items.filter((rec) => rec.status === filters.status);
      }
      if (filters.search) {
        const q = filters.search.toLowerCase();
        items = items.filter(
          (rec) =>
            rec.recordName.toLowerCase().includes(q) ||
            rec.code.toLowerCase().includes(q) ||
            (rec.referenceNumber && rec.referenceNumber.toLowerCase().includes(q)) ||
            (rec.issuingAuthority && rec.issuingAuthority.toLowerCase().includes(q))
        );
      }
    }

    return { success: true, data: items };
  }

  async getRecordById(id: string): Promise<ApiResponse<InstitutionalRecord | null>> {
    await new Promise((r) => setTimeout(r, 20));
    const rec = this.records.find((r) => r.id === id || r.code === id) || null;
    return { success: true, data: rec };
  }

  async createRecord(
    data: Partial<InstitutionalRecord>
  ): Promise<ApiResponse<InstitutionalRecord>> {
    await new Promise((r) => setTimeout(r, 60));
    const newRecord: InstitutionalRecord = {
      id: `rec-inst-${Date.now()}`,
      recordName: data.recordName || "New Institutional Record",
      code: data.code || `REC-GOV-${Date.now().toString().slice(-4)}`,
      category: data.category || "Policies & Governance",
      ownerDepartment: data.ownerDepartment || "Institutional Administration",
      confidentiality: data.confidentiality || ConfidentialityLevel.INTERNAL,
      status: data.status || InstitutionalRecordStatus.ACTIVE,
      createdDate: new Date().toISOString().split("T")[0],
      validUntil: data.validUntil,
      issuingAuthority: data.issuingAuthority || "Office of the Registrar",
      referenceNumber: data.referenceNumber,
      description: data.description,
      fileType: "application/pdf",
      fileSize: "2.4 MB",
      relatedDocuments: data.relatedDocuments || [],
      activity: [
        {
          id: `iact-${Date.now()}`,
          action: "Record Gazetted & Registered",
          performedBy: "Dr. Arvind Swaminathan (Registrar)",
          timestamp: new Date().toISOString(),
          details: "Added to institutional document register.",
        },
      ],
    };

    this.records.unshift(newRecord);
    return { success: true, data: newRecord };
  }

  async updateRecord(
    id: string,
    data: Partial<InstitutionalRecord>
  ): Promise<ApiResponse<InstitutionalRecord>> {
    await new Promise((r) => setTimeout(r, 50));
    const rec = this.records.find((r) => r.id === id);
    if (!rec) {
      throw new Error(`Institutional record with ID ${id} not found`);
    }

    Object.assign(rec, data);
    rec.activity.unshift({
      id: `iact-${Date.now()}`,
      action: "Record Amended",
      performedBy: "Dr. Arvind Swaminathan (Registrar)",
      timestamp: new Date().toISOString(),
      details: "Metadata and validity constraints updated.",
    });

    return { success: true, data: rec };
  }
}

export const institutionalRecordsService = new InstitutionalRecordsService();
