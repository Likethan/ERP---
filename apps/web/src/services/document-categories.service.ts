import {
  ApiResponse,
  DocumentCategory,
  DocumentCategoryCode,
} from "@campusos/types";
import { MOCK_DOCUMENT_CATEGORIES } from "@/mocks/documents.mock";

class DocumentCategoriesService {
  private categories: DocumentCategory[] = [...MOCK_DOCUMENT_CATEGORIES];

  async listCategories(): Promise<ApiResponse<DocumentCategory[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: [...this.categories] };
  }

  async getCategoryById(
    id: string,
  ): Promise<ApiResponse<DocumentCategory | null>> {
    await new Promise((r) => setTimeout(r, 20));
    const cat = this.categories.find((c) => c.id === id) || null;
    return { success: true, data: cat };
  }

  async getCategoryByCode(
    code: DocumentCategoryCode,
  ): Promise<ApiResponse<DocumentCategory | null>> {
    await new Promise((r) => setTimeout(r, 20));
    const cat = this.categories.find((c) => c.code === code) || null;
    return { success: true, data: cat };
  }

  async createCategory(
    data: Partial<DocumentCategory>,
  ): Promise<ApiResponse<DocumentCategory>> {
    await new Promise((r) => setTimeout(r, 60));
    const newCategory: DocumentCategory = {
      id: `cat-${Date.now()}`,
      name: data.name || "New Category",
      code: (data.code as DocumentCategoryCode) || DocumentCategoryCode.OTHER,
      description: data.description || "",
      required: data.required ?? false,
      applicableRoles: data.applicableRoles || ["STUDENT", "FACULTY", "STAFF"],
      applicableDocumentTypes: data.applicableDocumentTypes || [
        "General Record",
      ],
      verificationRequired: data.verificationRequired ?? true,
      expiryRequired: data.expiryRequired ?? false,
      isActive: true,
      totalDocuments: 0,
      verifiedDocuments: 0,
      pendingDocuments: 0,
      rejectedDocuments: 0,
      auditHistory: [
        {
          id: `aud-${Date.now()}`,
          action: "Category Created",
          performedBy: "Dr. Arvind Swaminathan (Registrar)",
          timestamp: new Date().toISOString(),
          details: "Configured via Institutional Document Governance",
        },
      ],
    };

    this.categories.push(newCategory);
    return { success: true, data: newCategory };
  }

  async updateCategory(
    id: string,
    data: Partial<DocumentCategory>,
  ): Promise<ApiResponse<DocumentCategory>> {
    await new Promise((r) => setTimeout(r, 50));
    const cat = this.categories.find((c) => c.id === id);
    if (!cat) {
      throw new Error(`Category with ID ${id} not found`);
    }

    Object.assign(cat, data);
    if (!cat.auditHistory) cat.auditHistory = [];
    cat.auditHistory.unshift({
      id: `aud-${Date.now()}`,
      action: "Rules Updated",
      performedBy: "Dr. Arvind Swaminathan (Registrar)",
      timestamp: new Date().toISOString(),
      details: "Category rules and role applicability modified.",
    });

    return { success: true, data: cat };
  }
}

export const documentCategoriesService = new DocumentCategoriesService();
