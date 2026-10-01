import { ApiResponse } from "@campusos/types";

export interface AiChatMessage {
  id: string;
  sender: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  suggestedActions?: Array<{
    label: string;
    href: string;
  }>;
}

export interface AiAssistantContext {
  role: string;
  userName: string;
  department?: string;
}

export interface IAiService {
  sendMessage(message: string, context?: AiAssistantContext): Promise<ApiResponse<AiChatMessage>>;
  getPresetPrompts(role?: string): string[];
}

/**
 * Mock AI Provider implementation demonstrating future conversational workflow
 * Explicitly demarcated as mock preview without pretending real AI exists.
 */
class MockAiService implements IAiService {
  getPresetPrompts(role = "SUPER_ADMIN"): string[] {
    switch (role) {
      case "STUDENT":
        return [
          "What is my current attendance percentage in CS301?",
          "Show my upcoming Continuous Internal Assessment timetable",
          "Are there any pending fee dues on my account?",
          "Which placement drives am I currently eligible for?",
        ];
      case "FACULTY":
        return [
          "List my lectures and lab sessions scheduled for today",
          "Show pending attendance sessions awaiting marking",
          "Generate low attendance warning list for 5th Sem CSE Sec A",
        ];
      case "HOD":
        return [
          "Summarize departmental attendance trends for CSE this week",
          "Show faculty teaching workload distribution across sections",
          "What is the current Tier-1 placement conversion in CSE?",
        ];
      case "ACCOUNTS":
        return [
          "What is the total fee collection vs overdue amount for 2026-27?",
          "List students with pending dues exceeding ₹30,000",
        ];
      default:
        return [
          "Provide institutional executive health overview for 2026-2027",
          "Show high-priority operational alerts across campus domains",
          "Summarize hostel occupancy and vacant bed capacity",
          "What is the average campus-wide attendance this semester?",
        ];
    }
  }

  async sendMessage(message: string, context?: AiAssistantContext): Promise<ApiResponse<AiChatMessage>> {
    await new Promise((r) => setTimeout(r, 600)); // Natural simulated latency

    const lower = message.toLowerCase();
    let reply = "";
    let actions: Array<{ label: string; href: string }> | undefined;

    if (lower.includes("attendance")) {
      reply = `According to verified attendance records for the 2026–2027 academic session, the consolidated campus-wide attendance stands at **87.6%**. In your department (CSE), 18 students in 5th Semester Section B have fallen below the mandatory 75% threshold and require academic counselor intervention.`;
      actions = [
        { label: "Open Attendance Dashboard", href: "/app/attendance" },
        { label: "Inspect Low Attendance Roster", href: "/app/attendance" },
      ];
    } else if (lower.includes("fee") || lower.includes("due") || lower.includes("revenue")) {
      reply = `Financial summary as of today: Total annual billed tuition & residential fees is **₹31.2 Cr**, with **92.4%** successfully cleared. Outstanding student receivables stand at **₹2.56 Cr** across 84 installment invoices.`;
      actions = [
        { label: "View Fee Invoices", href: "/app/finance/invoices" },
        { label: "Fee Structures", href: "/app/finance/fee-structures" },
      ];
    } else if (lower.includes("placement") || lower.includes("drive") || lower.includes("cisco") || lower.includes("offer")) {
      reply = `Career & Corporate Placement Cell Status: **3 active drives** currently in progress (Cisco Systems, Microsoft India R&D, TCS Digital). Overall 2026–27 Tier-1/2 placement rate is **84.2%** with highest verified package of **₹24.0 LPA** (Microsoft Cloud).`;
      actions = [
        { label: "Placement Dashboard", href: "/app/placement" },
        { label: "Inspect Candidate Shortlists", href: "/app/placement" },
      ];
    } else if (lower.includes("exam") || lower.includes("cia") || lower.includes("schedule") || lower.includes("test")) {
      reply = `Examinations & Evaluation Update: The Continuous Internal Assessment 1 (CIA-1) begins on **12th October 2026**. Seating allocations for 5th Semester CSE have been generated in Auditorium Hall A. CIA-1 marks entry windows will open on 15th October.`;
      actions = [
        { label: "View Exam Schedules", href: "/app/examinations/schedules" },
        { label: "Semester Results", href: "/app/examinations/results" },
      ];
    } else if (lower.includes("hostel") || lower.includes("room") || lower.includes("bed")) {
      reply = `Residential Infrastructure: Campus hostels are operating at **94.2% occupancy** (468 of 500 beds allocated). Sir C. V. Raman Hall (Boys) has 14 beds available; Kalpana Chawla Hall (Girls) has 12 beds available.`;
      actions = [
        { label: "Hostel Overview", href: "/app/hostel" },
      ];
    } else {
      reply = `[Demo AI Assistant]: Received query: "${message}". In the connected production environment, this query is processed via the CampusOS Institutional Knowledge Engine with granular Role-Based Access Control (PBAC), surfacing real-time verified data directly from PostgreSQL.`;
      actions = [
        { label: "Institutional Overview", href: "/app/dashboard" },
        { label: "Campus Intelligence", href: "/app/intelligence" },
      ];
    }

    const aiMessage: AiChatMessage = {
      id: `ai-msg-${Date.now()}`,
      sender: "assistant",
      content: reply,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      suggestedActions: actions,
    };

    return {
      success: true,
      data: aiMessage,
    };
  }
}

export const aiService: IAiService = new MockAiService();
