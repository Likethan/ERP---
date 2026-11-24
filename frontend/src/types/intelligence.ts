export * from "@campusos/types";

export interface IntelligenceFilterState {
  domain?: string;
  priority?: string;
  status?: string;
  search?: string;
  dateRange?: string;
}

export interface AssistantUIState {
  activeConversationId: string | null;
  selectedDomain: string;
  selectedContext: {
    type: "STUDENT" | "DEPARTMENT" | "COURSE" | "HOSTEL" | "ALL";
    id?: string;
    label: string;
  };
  isStreaming: boolean;
}
