import { ApiResponse } from "@campusos/types";
import {
  AnalyticsQuery,
  AnalyticsResult,
  IntelligenceDomain,
} from "@campusos/types";

class AiAnalyticsService {
  async runAnalyticsQuery(
    query: AnalyticsQuery,
  ): Promise<ApiResponse<AnalyticsResult>> {
    await new Promise((r) => setTimeout(r, 60));

    switch (query.domain) {
      case IntelligenceDomain.ATTENDANCE:
        return {
          success: true,
          data: {
            query,
            title: "Department-wise Attendance Distribution",
            summary:
              "Average attendance across departments with high-risk cohort highlights.",
            chartType: "bar",
            labels: ["CSE", "AI&DS", "ECE", "ME", "Civil", "IT"],
            datasets: [
              {
                name: "Average Attendance (%)",
                data: [84.6, 82.1, 88.1, 79.2, 81.5, 86.0],
                color: "#3b82f6",
              },
              {
                name: "Students < 75%",
                data: [18, 12, 6, 22, 14, 8],
                color: "#ef4444",
              },
            ],
            tableData: {
              headers: [
                "Department",
                "Enrolled",
                "Average Attendance",
                "Risk Count",
                "Status",
              ],
              rows: [
                ["Computer Science", 720, "84.6%", 18, "Normal"],
                ["AI & Data Science", 360, "82.1%", 12, "Normal"],
                ["Electronics & Comm", 480, "88.1%", 6, "Excellent"],
                ["Mechanical Engg", 320, "79.2%", 22, "Attention"],
                ["Civil Engg", 210, "81.5%", 14, "Normal"],
                ["Information Tech", 190, "86.0%", 8, "Good"],
              ],
            },
          },
        };

      case IntelligenceDomain.FINANCE:
        return {
          success: true,
          data: {
            query,
            title: "Billed vs Realized Fee Revenue",
            summary:
              "Semester fee collection performance against ₹33.7 Cr budget.",
            chartType: "bar",
            labels: ["Tuition", "Hostel & Mess", "Transport", "Exam & Lab"],
            datasets: [
              {
                name: "Billed (₹ Cr)",
                data: [22.5, 5.8, 3.2, 2.2],
                color: "#64748b",
              },
              {
                name: "Collected (₹ Cr)",
                data: [20.8, 5.4, 3.0, 2.0],
                color: "#10b981",
              },
            ],
            tableData: {
              headers: [
                "Fee Head",
                "Billed (Cr)",
                "Collected (Cr)",
                "Outstanding (Cr)",
                "Collection %",
              ],
              rows: [
                ["Tuition Fees", "₹22.5 Cr", "₹20.8 Cr", "₹1.70 Cr", "92.4%"],
                ["Hostel & Mess", "₹5.8 Cr", "₹5.4 Cr", "₹0.40 Cr", "93.1%"],
                [
                  "Transport Services",
                  "₹3.2 Cr",
                  "₹3.0 Cr",
                  "₹0.20 Cr",
                  "93.8%",
                ],
                [
                  "Exam & Lab Charges",
                  "₹2.2 Cr",
                  "₹2.0 Cr",
                  "₹0.20 Cr",
                  "90.9%",
                ],
              ],
            },
          },
        };

      case IntelligenceDomain.PLACEMENT:
        return {
          success: true,
          data: {
            query,
            title: "Recruitment Funnel & CTC Distribution",
            summary:
              "Placement conversion across Tier 1, Tier 2, and Core companies.",
            chartType: "line",
            labels: ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            datasets: [
              {
                name: "Candidates Applied",
                data: [420, 510, 680, 720, 750, 780],
                color: "#6366f1",
              },
              {
                name: "Offers Released",
                data: [65, 140, 290, 410, 480, 520],
                color: "#10b981",
              },
            ],
            tableData: {
              headers: [
                "Recruiter Category",
                "Drives Held",
                "Students Placed",
                "Highest CTC",
                "Average CTC",
              ],
              rows: [
                [
                  "Tier-1 Product (Google, MS)",
                  4,
                  38,
                  "₹24.0 LPA",
                  "₹18.5 LPA",
                ],
                ["Tier-2 Services & FinTech", 12, 184, "₹14.2 LPA", "₹9.8 LPA"],
                ["Mass Recruiters (TCS, Infy)", 6, 210, "₹7.5 LPA", "₹5.2 LPA"],
                ["Core Engineering", 8, 88, "₹9.0 LPA", "₹6.4 LPA"],
              ],
            },
          },
        };

      case IntelligenceDomain.INFRASTRUCTURE:
        return {
          success: true,
          data: {
            query,
            title: "Residential & Transport Asset Utilization",
            summary:
              "Hostel capacity, bus circuit loads, and work order turnaround.",
            chartType: "donut",
            labels: [
              "Block A (Boys)",
              "Block B (Girls)",
              "Block C (PG)",
              "Staff Quarters",
            ],
            datasets: [
              {
                name: "Occupancy Rate (%)",
                data: [96.0, 92.5, 88.0, 84.0],
                color: "#f59e0b",
              },
            ],
            tableData: {
              headers: [
                "Asset Category",
                "Total Capacity",
                "Currently Allocated",
                "Utilization",
                "Open Issues",
              ],
              rows: [
                [
                  "Sir C.V. Raman Hall (Block A)",
                  "200 Beds",
                  "192 Beds",
                  "96.0%",
                  "2 Plumbing",
                ],
                [
                  "Kalpana Chawla Hall (Block B)",
                  "180 Beds",
                  "166 Beds",
                  "92.2%",
                  "1 Electrical",
                ],
                [
                  "Dr. APJ Abdul Kalam Hall",
                  "120 Beds",
                  "106 Beds",
                  "88.3%",
                  "0 Issues",
                ],
                [
                  "Bus Circuit North Line",
                  "160 Seats",
                  "152 Passes",
                  "95.0%",
                  "0 Issues",
                ],
              ],
            },
          },
        };

      default:
        return {
          success: true,
          data: {
            query,
            title: "Cross-Domain Institutional Analytics",
            summary:
              "Consolidated performance indices across academics, attendance, and placement.",
            chartType: "bar",
            labels: [
              "Academics",
              "Attendance",
              "Finance",
              "Placement",
              "Infrastructure",
              "Documents",
            ],
            datasets: [
              {
                name: "Health Score (0-100)",
                data: [92, 84, 86, 94, 87, 90],
                color: "#3b82f6",
              },
            ],
            tableData: {
              headers: ["Domain", "Score", "Trend", "Status", "Open Alerts"],
              rows: [
                ["Academics", "92/100", "+1.8%", "Excellent", "1 Alert"],
                ["Attendance", "84/100", "+1.2%", "Good", "2 Alerts"],
                ["Finance", "86/100", "+0.8%", "Good", "1 Alert"],
                ["Placement", "94/100", "+5.6%", "Excellent", "0 Alerts"],
                ["Infrastructure", "87/100", "Stable", "Good", "1 Alert"],
                ["Documents", "90/100", "+2.0%", "Excellent", "1 Alert"],
              ],
            },
          },
        };
    }
  }
}

export const aiAnalyticsService = new AiAnalyticsService();
