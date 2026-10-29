import { ApiResponse } from "@campusos/types";
import {
  AIQuery,
  AIResponse,
  AIResponseBlockType,
  IntelligenceDomain,
  AIActivityStatus,
} from "@campusos/types";
import { aiActivityService } from "./ai-activity.service";
import { aiToolsService } from "./ai-tools.service";

class AiAssistantService {
  getSuggestedPrompts(
    role = "SUPER_ADMIN",
  ): { label: string; query: string; domain: IntelligenceDomain }[] {
    switch (role) {
      case "STUDENT":
        return [
          {
            label: "My Attendance",
            query: "What is my current attendance percentage?",
            domain: IntelligenceDomain.ATTENDANCE,
          },
          {
            label: "Exam Schedule",
            query: "What exams are scheduled for me this week?",
            domain: IntelligenceDomain.EXAMINATIONS,
          },
          {
            label: "Pending Dues",
            query: "Are there any pending fee invoices on my account?",
            domain: IntelligenceDomain.FINANCE,
          },
          {
            label: "Eligible Drives",
            query: "Which campus placement drives am I eligible for?",
            domain: IntelligenceDomain.PLACEMENT,
          },
          {
            label: "My Documents",
            query: "Are any of my uploaded documents expiring soon?",
            domain: IntelligenceDomain.DOCUMENTS,
          },
        ];

      case "FACULTY":
        return [
          {
            label: "Class Attendance",
            query: "Show low attendance students in my course",
            domain: IntelligenceDomain.ATTENDANCE,
          },
          {
            label: "CIA-1 Marks",
            query: "What is the deadline for CIA-1 marks submission?",
            domain: IntelligenceDomain.EXAMINATIONS,
          },
          {
            label: "My Schedule",
            query: "Show my lecture and lab timetable for today",
            domain: IntelligenceDomain.ACADEMICS,
          },
        ];

      case "HOD":
        return [
          {
            label: "Attendance Below 75%",
            query: "Which students have attendance below 75%?",
            domain: IntelligenceDomain.ATTENDANCE,
          },
          {
            label: "Placement by Dept",
            query: "Show placement applications and conversion by department",
            domain: IntelligenceDomain.PLACEMENT,
          },
          {
            label: "Department Health",
            query: "Summarize department health and faculty workload",
            domain: IntelligenceDomain.ACADEMICS,
          },
        ];

      case "ACCOUNTS":
        return [
          {
            label: "Overdue Fees",
            query: "Which fees are overdue this semester?",
            domain: IntelligenceDomain.FINANCE,
          },
          {
            label: "Revenue Realized",
            query: "Show fee collection performance vs annual targets",
            domain: IntelligenceDomain.FINANCE,
          },
        ];

      case "PLACEMENT_OFFICER":
        return [
          {
            label: "Placement Summary",
            query: "Summarize placement activity this month",
            domain: IntelligenceDomain.PLACEMENT,
          },
          {
            label: "Eligible Candidates",
            query: "Which students are eligible for Cisco Systems drive?",
            domain: IntelligenceDomain.PLACEMENT,
          },
        ];

      default:
        // Admin / Registrar
        return [
          {
            label: "Attendance Below 75%",
            query: "Which students have attendance below 75%?",
            domain: IntelligenceDomain.ATTENDANCE,
          },
          {
            label: "Placement by Dept",
            query: "Show placement applications by department",
            domain: IntelligenceDomain.PLACEMENT,
          },
          {
            label: "Overdue Fees",
            query: "Which fees are overdue this semester?",
            domain: IntelligenceDomain.FINANCE,
          },
          {
            label: "Exams This Week",
            query: "What exams are scheduled this week?",
            domain: IntelligenceDomain.EXAMINATIONS,
          },
          {
            label: "Hostel Complaints",
            query: "Which hostel complaints are still unresolved?",
            domain: IntelligenceDomain.INFRASTRUCTURE,
          },
          {
            label: "Placement Activity",
            query: "Summarize placement activity this month",
            domain: IntelligenceDomain.PLACEMENT,
          },
          {
            label: "Expiring Documents",
            query: "Which documents are expiring soon?",
            domain: IntelligenceDomain.DOCUMENTS,
          },
          {
            label: "Cross-Domain Risk",
            query: "Which students have low attendance and outstanding fees?",
            domain: IntelligenceDomain.ALL,
          },
        ];
    }
  }

  async sendQuery(payload: AIQuery): Promise<ApiResponse<AIResponse>> {
    const startTime = Date.now();
    await new Promise((r) => setTimeout(r, 450)); // Fast deterministic simulated thinking time

    const q = payload.query.toLowerCase().trim();
    const role = payload.context?.role || "SUPER_ADMIN";

    // Permission check: Students cannot access institution-wide administrative aggregates
    if (role === "STUDENT") {
      if (
        q.includes("all students") ||
        q.includes("institution revenue") ||
        q.includes("faculty salary") ||
        q.includes("by department")
      ) {
        const duration = Date.now() - startTime;
        return {
          success: true,
          data: {
            id: `resp-${Date.now().toString(36)}`,
            query: payload.query,
            reply:
              "Permission Restricted: Your student account is authorized for personal academic records only. Administrative telemetry across departments requires faculty or administrative clearance.",
            blocks: [
              {
                type: AIResponseBlockType.WARNING,
                title: "Access Restricted",
                content:
                  "You do not have permission to view institutional aggregates. You can ask questions about your personal attendance, enrolled courses, fee invoices, placement drives, and verified documents.",
              },
            ],
            sources: [],
            explainability: {
              dataSources: ["rbac_policy_engine"],
              filtersApplied: ["Role: STUDENT", "Scope: Personal Only"],
              timePeriod: "Current Session",
              calculationUsed: "Permission Evaluation",
              threshold: "Role === STUDENT",
              result: "DENIED",
            },
            suggestedActions: [
              { label: "My Attendance", href: "/app/attendance" },
              { label: "My Exam Grades", href: "/app/examinations/results" },
              { label: "My Documents", href: "/app/documents/my-documents" },
            ],
            executionTimeMs: duration,
          },
        };
      }
    }

    // 1. Cross-Domain: Low Attendance + Outstanding Fees
    if (
      (q.includes("attendance") && q.includes("fee")) ||
      (q.includes("attendance") && q.includes("due"))
    ) {
      const resp = this.buildLowAttendanceAndFeesResponse(payload.query);
      await this.recordActivity(payload, resp, [
        "get_attendance_summary",
        "get_fee_summary",
      ]);
      return { success: true, data: resp };
    }

    // 2. Cross-Domain: Placement Eligibility + Missing Documents
    if (
      (q.includes("placement") && q.includes("doc")) ||
      (q.includes("placement") && q.includes("verif"))
    ) {
      const resp = this.buildPlacementAndDocsResponse(payload.query);
      await this.recordActivity(payload, resp, [
        "get_placement_summary",
        "get_document_status",
      ]);
      return { success: true, data: resp };
    }

    // 3. Attendance Queries
    if (q.includes("attendance") || q.includes("75%")) {
      const resp = this.buildAttendanceResponse(payload.query);
      await this.recordActivity(payload, resp, [
        "get_attendance_summary",
        "get_student_profile",
      ]);
      return { success: true, data: resp };
    }

    // 4. Finance / Fees Queries
    if (
      q.includes("fee") ||
      q.includes("due") ||
      q.includes("overdue") ||
      q.includes("revenue") ||
      q.includes("collect")
    ) {
      const resp = this.buildFinanceResponse(payload.query);
      await this.recordActivity(payload, resp, ["get_fee_summary"]);
      return { success: true, data: resp };
    }

    // 5. Placement Queries
    if (
      q.includes("placement") ||
      q.includes("drive") ||
      q.includes("cisco") ||
      q.includes("package") ||
      q.includes("offer")
    ) {
      const resp = this.buildPlacementResponse(payload.query);
      await this.recordActivity(payload, resp, [
        "get_placement_summary",
        "get_department_metrics",
      ]);
      return { success: true, data: resp };
    }

    // 6. Examination Queries
    if (
      q.includes("exam") ||
      q.includes("cia") ||
      q.includes("schedule") ||
      q.includes("mark") ||
      q.includes("grade")
    ) {
      const resp = this.buildExamResponse(payload.query);
      await this.recordActivity(payload, resp, [
        "get_exam_schedule",
        "get_student_result",
      ]);
      return { success: true, data: resp };
    }

    // 7. Infrastructure / Hostel / Transport Queries
    if (
      q.includes("hostel") ||
      q.includes("complaint") ||
      q.includes("bed") ||
      q.includes("bus") ||
      q.includes("transport")
    ) {
      const resp = this.buildInfrastructureResponse(payload.query);
      await this.recordActivity(payload, resp, [
        "get_hostel_status",
        "get_transport_allocation",
      ]);
      return { success: true, data: resp };
    }

    // 8. Documents / Verification Queries
    if (
      q.includes("document") ||
      q.includes("cert") ||
      q.includes("expir") ||
      q.includes("verif")
    ) {
      const resp = this.buildDocumentsResponse(payload.query);
      await this.recordActivity(payload, resp, ["get_document_status"]);
      return { success: true, data: resp };
    }

    // 9. Default Executive Synthesis
    const resp = this.buildCampusSummaryResponse(payload.query);
    await this.recordActivity(payload, resp, ["get_campus_metrics"]);
    return { success: true, data: resp };
  }

  private async recordActivity(
    query: AIQuery,
    response: AIResponse,
    tools: string[],
  ) {
    await aiActivityService.logActivity({
      userName: query.context?.userName || "Administrator",
      userRole: query.context?.role || "SUPER_ADMIN",
      query: query.query,
      domain: query.domain || IntelligenceDomain.ALL,
      toolsInvoked: tools,
      resultSummary: response.reply.slice(0, 100),
      durationMs: response.executionTimeMs,
      status: AIActivityStatus.COMPLETED,
      dataSources: response.sources.map((s) => s.name),
      contextSummary: query.context?.departmentId || "Campus-wide",
    });

    for (const tool of tools) {
      await aiToolsService.logExecution({
        toolName: tool,
        user: query.context?.userName || "Administrator",
        role: query.context?.role || "SUPER_ADMIN",
        durationMs: Math.round(response.executionTimeMs / tools.length),
        status: "SUCCESS",
      });
    }
  }

  private buildAttendanceResponse(query: string): AIResponse {
    return {
      id: `resp-${Date.now().toString(36)}`,
      query,
      reply:
        "18 students currently have consolidated attendance below the configured 75% examination eligibility threshold across active lecture and laboratory sessions.",
      blocks: [
        {
          type: AIResponseBlockType.METRIC,
          metrics: [
            {
              label: "Total Students <75%",
              value: 18,
              change: "-4 vs last term",
              trend: "up",
            },
            {
              label: "Critical (<60%)",
              value: 3,
              change: "Detention risk",
              trend: "down",
            },
            {
              label: "Campus Average",
              value: "86.8%",
              change: "+1.2%",
              trend: "up",
            },
          ],
        },
        {
          type: AIResponseBlockType.TABLE,
          title: "Attendance Risk Distribution by Department",
          table: {
            headers: ["Department", "Semester", "Affected Count", "Risk Level"],
            rows: [
              ["Computer Science & Engineering", "Sem 5 Sec B", 7, "HIGH"],
              [
                "Artificial Intelligence & Data Science",
                "Sem 3 Sec A",
                5,
                "HIGH",
              ],
              ["Electronics & Communication", "Sem 5 Sec A", 3, "MEDIUM"],
              ["Mechanical Engineering", "Sem 7 Sec A", 3, "CRITICAL"],
            ],
          },
        },
        {
          type: AIResponseBlockType.RECOMMENDATION,
          title: "Recommended Actions",
          list: [
            "Review attendance records for the 3 students below 60% with academic counselors.",
            "Verify medical certificates on file in Digital Records repository for condonation claims.",
            "Notify affected students and guardians prior to examination hall ticket freezing.",
          ],
        },
      ],
      sources: [
        {
          name: "Attendance Sessions Register",
          domain: IntelligenceDomain.ATTENDANCE,
          href: "/app/attendance",
          description: "Consolidated roll-call sheets",
        },
        {
          name: "Student Dossier Roster",
          domain: IntelligenceDomain.PEOPLE,
          href: "/app/students",
          description: "Active student cohorts",
        },
      ],
      explainability: {
        dataSources: [
          "attendance_sessions",
          "attendance_records",
          "students_master",
        ],
        filtersApplied: [
          "Academic Term: 2026-27",
          "Attendance Percentage < 75.0%",
        ],
        timePeriod: "Current Term (1 Aug 2026 – 2 Oct 2026)",
        calculationUsed: "SUM(Present Hours) / SUM(Enrolled Hours) * 100",
        threshold: "75.0% Institutional Minimum",
        result: "18 Students (3 Critical, 15 Elevated)",
      },
      suggestedActions: [
        { label: "Open Attendance Roster", href: "/app/attendance" },
        { label: "Review Leave Requests", href: "/app/attendance/leaves" },
      ],
      executionTimeMs: 410,
      toolName: "get_attendance_summary",
    };
  }

  private buildFinanceResponse(query: string): AIResponse {
    return {
      id: `resp-${Date.now().toString(36)}`,
      query,
      reply:
        "For the 2026-2027 academic session, ₹31.2 Cr has been collected against ₹33.7 Cr billed (92.4% clearance). Outstanding receivables stand at ₹2.56 Cr across 84 installment invoices, with ₹42.8 Lakhs overdue by >30 days.",
      blocks: [
        {
          type: AIResponseBlockType.METRIC,
          metrics: [
            {
              label: "Total Billed",
              value: "₹33.7 Cr",
              change: "+6.2% YoY",
              trend: "up",
            },
            {
              label: "Collected to Date",
              value: "₹31.2 Cr",
              change: "92.4% cleared",
              trend: "up",
            },
            {
              label: "Overdue (>30 Days)",
              value: "₹42.8 L",
              change: "36 Invoices",
              trend: "down",
            },
          ],
        },
        {
          type: AIResponseBlockType.TABLE,
          title: "Overdue Invoices Aging Breakdown",
          table: {
            headers: [
              "Aging Bucket",
              "Invoice Count",
              "Total Amount",
              "Primary Department",
            ],
            rows: [
              ["1 – 30 Days Overdue", 48, "₹2,13,20,000", "Mechanical Engg"],
              ["31 – 60 Days Overdue", 24, "₹31,40,000", "Civil Engg"],
              ["> 60 Days Overdue", 12, "₹11,40,000", "Electronics & Comm"],
            ],
          },
        },
        {
          type: AIResponseBlockType.RECOMMENDATION,
          title: "Recommended Operational Actions",
          list: [
            "Dispatch automated SMS & email installment payment links to the 36 overdue accounts.",
            "Schedule accounts consultation for students eligible for merit-cum-means concessions.",
            "Review fee clearance exemptions prior to upcoming End-Semester hall ticket generation.",
          ],
        },
      ],
      sources: [
        {
          name: "Student Invoices Register",
          domain: IntelligenceDomain.FINANCE,
          href: "/app/finance/invoices",
          description: "All semester fee billings",
        },
        {
          name: "Payment Transactions Ledger",
          domain: IntelligenceDomain.FINANCE,
          href: "/app/finance/payments",
          description: "Gateway and counter collections",
        },
      ],
      explainability: {
        dataSources: [
          "fee_invoices",
          "payment_transactions",
          "scholarship_allocations",
        ],
        filtersApplied: ["Academic Year: 2026-2027", "Invoice Status: OVERDUE"],
        timePeriod: "Current Academic Year (2026-27)",
        calculationUsed:
          "SUM(Total Amount) - SUM(Paid Amount) WHERE dueDate < NOW()",
        threshold: "Due Date Exceeded",
        result: "₹2.56 Cr Total Pending (₹42.8 L > 30 Days)",
      },
      suggestedActions: [
        { label: "Inspect Overdue Invoices", href: "/app/finance/invoices" },
        { label: "View Fee Structures", href: "/app/finance/fee-structures" },
      ],
      executionTimeMs: 440,
      toolName: "get_fee_summary",
    };
  }

  private buildPlacementResponse(query: string): AIResponse {
    return {
      id: `resp-${Date.now().toString(36)}`,
      query,
      reply:
        "Placement Cell status: 3 active recruitment drives are underway (Cisco Systems, Microsoft India R&D, TCS Digital). Overall 2026-27 Tier 1/2 conversion is 84.2% with 290 candidate offers issued and average CTC of ₹12.4 LPA.",
      blocks: [
        {
          type: AIResponseBlockType.METRIC,
          metrics: [
            {
              label: "Placement Rate",
              value: "84.2%",
              change: "+5.6% vs 2025",
              trend: "up",
            },
            {
              label: "Offers Released",
              value: 290,
              change: "Across 48 companies",
              trend: "up",
            },
            {
              label: "Highest Package",
              value: "₹24.0 LPA",
              change: "Microsoft Cloud",
              trend: "up",
            },
          ],
        },
        {
          type: AIResponseBlockType.TABLE,
          title: "Active Recruitment Drives (October 2026)",
          table: {
            headers: [
              "Company",
              "Drive Type",
              "Eligible",
              "Shortlisted",
              "Status",
            ],
            rows: [
              [
                "Cisco Systems India",
                "Product Tier-1",
                124,
                28,
                "Technical Round 2",
              ],
              [
                "Microsoft India R&D",
                "Product Tier-1",
                86,
                14,
                "Final Partner Round",
              ],
              [
                "TCS Digital",
                "FinTech / IT",
                310,
                142,
                "Online Assessment Complete",
              ],
            ],
          },
        },
        {
          type: AIResponseBlockType.RECOMMENDATION,
          title: "Recommended Placement Actions",
          list: [
            "Follow up with 28 Cisco Systems technical round candidates for mock coding preparation.",
            "Verify digital record marksheets for 8 shortlisted candidates with pending verifications.",
            "Coordinate with company HR for campus onboarding briefing next Tuesday.",
          ],
        },
      ],
      sources: [
        {
          name: "Corporate Drives Catalog",
          domain: IntelligenceDomain.PLACEMENT,
          href: "/app/placement",
          description: "Empanelled recruitment schedules",
        },
        {
          name: "Student Placement Dossiers",
          domain: IntelligenceDomain.PLACEMENT,
          href: "/app/placement",
          description: "Candidate resumes & verification flags",
        },
      ],
      explainability: {
        dataSources: [
          "placement_drives",
          "placement_applications",
          "placement_offers",
        ],
        filtersApplied: ["Term: 2026-2027", "Recruitment Status: ACTIVE"],
        timePeriod: "Current Drive Season (July – Dec 2026)",
        calculationUsed: "(Offers Released / Total Eligible Registered) * 100",
        threshold: "Eligible >= 7.0 CGPA & No Standing Backlogs",
        result: "84.2% Placement Rate across 290 Offers",
      },
      suggestedActions: [
        { label: "Open Placement Portal", href: "/app/placement" },
        { label: "Verify Resumes", href: "/app/documents/verification" },
      ],
      executionTimeMs: 380,
      toolName: "get_placement_summary",
    };
  }

  private buildExamResponse(query: string): AIResponse {
    return {
      id: `resp-${Date.now().toString(36)}`,
      query,
      reply:
        "Continuous Internal Assessment 1 (CIA-1) begins on 12th October 2026 across Auditorium Hall A and Main Block halls. 42 subject timetables are published; 2 course offerings await faculty marks roster confirmation.",
      blocks: [
        {
          type: AIResponseBlockType.METRIC,
          metrics: [
            {
              label: "Scheduled Exams",
              value: 42,
              change: "CIA-1 Cycle",
              trend: "neutral",
            },
            {
              label: "Seating Halls",
              value: 12,
              change: "100% Hall Capacity",
              trend: "up",
            },
            {
              label: "Pending Rosters",
              value: 2,
              change: "Due in 48 hours",
              trend: "down",
            },
          ],
        },
        {
          type: AIResponseBlockType.RECOMMENDATION,
          title: "Recommended Examination Actions",
          list: [
            "Issue invigilator roster to all assigned faculty members by Friday.",
            "Notify students of seat allocations in Auditorium Hall A.",
            "Send reminder to CS304 and ME401 instructors for CIA-1 question paper submission.",
          ],
        },
      ],
      sources: [
        {
          name: "Exam Schedules Register",
          domain: IntelligenceDomain.EXAMINATIONS,
          href: "/app/examinations/schedules",
          description: "Timetables and seating plans",
        },
      ],
      explainability: {
        dataSources: ["exam_schedules", "course_offerings"],
        filtersApplied: ["Exam Cycle: CIA-1", "Date Window: Next 14 Days"],
        timePeriod: "12 Oct 2026 – 20 Oct 2026",
        calculationUsed: "COUNT(Scheduled Subjects) + Hall Allocation Check",
        result: "42 Exam Sessions Scheduled",
      },
      suggestedActions: [
        { label: "View Exam Timetables", href: "/app/examinations/schedules" },
        { label: "Marks Entry Console", href: "/app/examinations/marks" },
      ],
      executionTimeMs: 360,
      toolName: "get_exam_schedule",
    };
  }

  private buildInfrastructureResponse(query: string): AIResponse {
    return {
      id: `resp-${Date.now().toString(36)}`,
      query,
      reply:
        "Campus infrastructure operational overview: Residential halls are at 94.2% occupancy (468 of 500 beds allocated). 3 maintenance complaints are open, with 1 high-priority plumbing leak in Block A currently assigned to standby staff.",
      blocks: [
        {
          type: AIResponseBlockType.METRIC,
          metrics: [
            {
              label: "Hostel Occupancy",
              value: "94.2%",
              change: "468 / 500 Beds",
              trend: "up",
            },
            {
              label: "Vacant Beds",
              value: 32,
              change: "14 Boys, 18 Girls",
              trend: "neutral",
            },
            {
              label: "Open Complaints",
              value: 3,
              change: "Avg SLA 3.4 hrs",
              trend: "up",
            },
          ],
        },
        {
          type: AIResponseBlockType.RECOMMENDATION,
          title: "Recommended Operations Actions",
          list: [
            "Follow up on Block A plumbing ticket CMP-HST-2026-102 with campus maintenance team.",
            "Hold 12 buffer beds in Block B for incoming exchange students.",
            "Inspect fleet fitness certificates for Bus Route North Line ahead of weekend trip.",
          ],
        },
      ],
      sources: [
        {
          name: "Hostel Allocations Register",
          domain: IntelligenceDomain.INFRASTRUCTURE,
          href: "/app/hostel",
          description: "Room and bed registry",
        },
        {
          name: "Maintenance Work Orders",
          domain: IntelligenceDomain.INFRASTRUCTURE,
          href: "/app/hostel",
          description: "Service desk tickets",
        },
      ],
      explainability: {
        dataSources: ["hostel_rooms", "hostel_complaints", "transport_routes"],
        filtersApplied: ["Status: Active", "Open Issues: True"],
        timePeriod: "Current Status",
        calculationUsed: "Allocated Beds / Total Registered Capacity * 100",
        result: "94.2% Occupancy, 3 Open Issues",
      },
      suggestedActions: [
        { label: "Open Hostel Management", href: "/app/hostel" },
        { label: "Transport Fleet", href: "/app/transport" },
      ],
      executionTimeMs: 390,
      toolName: "get_hostel_status",
    };
  }

  private buildDocumentsResponse(query: string): AIResponse {
    return {
      id: `resp-${Date.now().toString(36)}`,
      query,
      reply:
        "Digital records audit: 4 mandatory identity and category certificates expire within the next 30 days. The institutional verification queue currently has 3 pending submissions with an average turnaround SLA of 27 hours.",
      blocks: [
        {
          type: AIResponseBlockType.METRIC,
          metrics: [
            {
              label: "Expiring in 30 Days",
              value: 4,
              change: "Government category docs",
              trend: "down",
            },
            {
              label: "Pending Verification",
              value: 3,
              change: "Turnaround SLA 27h",
              trend: "up",
            },
            {
              label: "Verification Rate",
              value: "91.8%",
              change: "+2.0% this month",
              trend: "up",
            },
          ],
        },
        {
          type: AIResponseBlockType.RECOMMENDATION,
          title: "Recommended Document Actions",
          list: [
            "Notify students with caste and income certificates expiring before government portal deadlines.",
            "Expedite verification of transfer certificates for recently admitted lateral entrants.",
            "Process 2 pending bonafide certificate requests before end of day.",
          ],
        },
      ],
      sources: [
        {
          name: "Documents Repository",
          domain: IntelligenceDomain.DOCUMENTS,
          href: "/app/documents/all",
          description: "Master credentials catalog",
        },
        {
          name: "Verification Queue",
          domain: IntelligenceDomain.DOCUMENTS,
          href: "/app/documents/verification",
          description: "Active review items",
        },
      ],
      explainability: {
        dataSources: [
          "documents_master",
          "verification_queue",
          "certificate_requests",
        ],
        filtersApplied: [
          "Expiry Date < NOW() + 30 Days",
          "Status: UNDER_REVIEW",
        ],
        timePeriod: "Next 30 Days",
        calculationUsed: "COUNT(Documents WHERE expiryDate <= 30 Days)",
        result: "4 Expiring Documents, 3 Pending Verification",
      },
      suggestedActions: [
        {
          label: "Open Verification Queue",
          href: "/app/documents/verification",
        },
        {
          label: "Certificate Requests",
          href: "/app/documents/certificates/requests",
        },
      ],
      executionTimeMs: 370,
      toolName: "get_document_status",
    };
  }

  private buildLowAttendanceAndFeesResponse(query: string): AIResponse {
    return {
      id: `resp-${Date.now().toString(36)}`,
      query,
      reply:
        "Cross-domain analysis identified 4 students who concurrently exhibit both attendance below 75% and overdue tuition fee installments. These students require priority inter-departmental counseling.",
      blocks: [
        {
          type: AIResponseBlockType.WARNING,
          title: "Concurrent Risk Detected",
          content:
            "Students with dual attendance shortfalls and financial overdue status face heightened risk of examination detention and administrative hold.",
        },
        {
          type: AIResponseBlockType.TABLE,
          title: "Dual Risk Student Cohort",
          table: {
            headers: [
              "Student Name",
              "Roll No",
              "Department",
              "Attendance %",
              "Overdue Dues",
              "Status",
            ],
            rows: [
              [
                "Vikram Aditya",
                "23EC011",
                "Electronics & Comm",
                "58.6%",
                "₹32,000",
                "Critical",
              ],
              [
                "Rhea Sen",
                "22CS014",
                "Computer Science",
                "68.2%",
                "₹24,500",
                "High",
              ],
              [
                "Manish Gupta",
                "24ME008",
                "Mechanical Engg",
                "64.0%",
                "₹18,000",
                "High",
              ],
              [
                "Pooja Hegde",
                "23AD021",
                "AI & Data Science",
                "72.4%",
                "₹15,000",
                "Medium",
              ],
            ],
          },
        },
        {
          type: AIResponseBlockType.RECOMMENDATION,
          title: "Recommended Collaborative Actions",
          list: [
            "Convene joint academic mentor and accounts officer counseling session for Vikram Aditya.",
            "Verify if financial hardship is a contributing factor to lecture absenteeism.",
            "Establish structured fee installment roadmap before issuing exam hall tickets.",
          ],
        },
      ],
      sources: [
        {
          name: "Attendance Records",
          domain: IntelligenceDomain.ATTENDANCE,
          href: "/app/attendance",
          description: "Lecture & lab logs",
        },
        {
          name: "Student Invoices",
          domain: IntelligenceDomain.FINANCE,
          href: "/app/finance/invoices",
          description: "Billed fees & overdue aging",
        },
      ],
      explainability: {
        dataSources: ["attendance_records", "fee_invoices", "students_master"],
        filtersApplied: ["Attendance < 75.0%", "Invoice Status: OVERDUE"],
        timePeriod: "Current Semester (2026-27)",
        calculationUsed:
          "INNER JOIN students ON (attendance < 75% AND fee_overdue > 0)",
        threshold: "Dual criteria match",
        result: "4 Students Identified",
      },
      suggestedActions: [
        { label: "Inspect Attendance Roster", href: "/app/attendance" },
        { label: "Review Overdue Invoices", href: "/app/finance/invoices" },
      ],
      executionTimeMs: 480,
      toolName: "get_attendance_summary",
    };
  }

  private buildPlacementAndDocsResponse(query: string): AIResponse {
    return {
      id: `resp-${Date.now().toString(36)}`,
      query,
      reply:
        "8 students meeting company CGPA criteria (>= 8.0) for the upcoming Cisco Systems recruitment drive currently have unverified 10th/12th marksheets in the Digital Records repository.",
      blocks: [
        {
          type: AIResponseBlockType.WARNING,
          title: "Placement Gatekeeper Risk",
          content:
            "Recruiters mandate verified academic transcripts prior to technical interviews scheduled for 08 October 2026.",
        },
        {
          type: AIResponseBlockType.TABLE,
          title: "Candidates Requiring Document Verification",
          table: {
            headers: [
              "Candidate",
              "Roll No",
              "CGPA",
              "Missing / Unverified Document",
              "Drive",
            ],
            rows: [
              [
                "Aarav Patel",
                "22CS001",
                "8.42",
                "12th Standard Marksheet",
                "Cisco Systems",
              ],
              [
                "Siddharth Rao",
                "22CS029",
                "8.15",
                "10th Marksheet Re-upload",
                "Cisco Systems",
              ],
              [
                "Meera Nambiar",
                "22CS044",
                "8.65",
                "Bonafide Clearance",
                "Microsoft India",
              ],
              [
                "Ananya Sharma",
                "23EC044",
                "8.20",
                "Category Validity Proof",
                "Cisco Systems",
              ],
            ],
          },
        },
        {
          type: AIResponseBlockType.RECOMMENDATION,
          title: "Recommended Placement Actions",
          list: [
            "Expedite administrative verification queue for shortlisted placement candidates.",
            "Prompt candidates to resubmit unreadable credentials through the mobile upload workflow.",
            "Confirm corporate interview roster by Thursday 5:00 PM.",
          ],
        },
      ],
      sources: [
        {
          name: "Placement Candidates Roster",
          domain: IntelligenceDomain.PLACEMENT,
          href: "/app/placement",
          description: "Cisco drive applicants",
        },
        {
          name: "Documents Verification Queue",
          domain: IntelligenceDomain.DOCUMENTS,
          href: "/app/documents/verification",
          description: "Unverified records",
        },
      ],
      explainability: {
        dataSources: ["placement_applications", "documents_master"],
        filtersApplied: [
          "Drive: Cisco Systems",
          "Verification Status != VERIFIED",
        ],
        timePeriod: "Current Placement Season",
        calculationUsed:
          "Placement Shortlists CROSS REFERENCED WITH Unverified Documents",
        result: "8 Candidates with Document Gaps",
      },
      suggestedActions: [
        {
          label: "Open Verification Queue",
          href: "/app/documents/verification",
        },
        { label: "Placement Drive Details", href: "/app/placement" },
      ],
      executionTimeMs: 460,
      toolName: "get_placement_summary",
    };
  }

  private buildCampusSummaryResponse(query: string): AIResponse {
    return {
      id: `resp-${Date.now().toString(36)}`,
      query,
      reply:
        "CampusOS Executive Synthesis: Academic operations, consolidated attendance, tuition collections, and corporate placement conversions are all performing within normal or excellent parameters for the 2026-2027 academic session.",
      blocks: [
        {
          type: AIResponseBlockType.METRIC,
          metrics: [
            {
              label: "Campus Health",
              value: "88/100",
              change: "+2.4% MoM",
              trend: "up",
            },
            {
              label: "Total Students",
              value: "2,280",
              change: "100% Onboarded",
              trend: "up",
            },
            {
              label: "Placement Conversion",
              value: "84.2%",
              change: "290 Offers",
              trend: "up",
            },
          ],
        },
        {
          type: AIResponseBlockType.TABLE,
          title: "Domain Health Radar",
          table: {
            headers: ["Domain", "Primary Metric", "Health Score", "Status"],
            rows: [
              ["Academics", "92.4% Course Completion", "92/100", "EXCELLENT"],
              ["Attendance", "86.8% Average Attendance", "84/100", "GOOD"],
              ["Examinations", "42 CIA Exams Scheduled", "88/100", "GOOD"],
              ["Finance", "₹31.2 Cr Collected (92.4%)", "86/100", "GOOD"],
              ["Placement", "84.2% Placement Rate", "94/100", "EXCELLENT"],
              ["Infrastructure", "94.2% Hostel Occupancy", "87/100", "GOOD"],
              ["Documents", "91.8% Records Verified", "90/100", "EXCELLENT"],
            ],
          },
        },
      ],
      sources: [
        {
          name: "Campus Telemetry Engine",
          domain: IntelligenceDomain.ALL,
          href: "/app/intelligence",
          description: "Consolidated operational feeds",
        },
      ],
      explainability: {
        dataSources: ["all_campus_subsystems"],
        filtersApplied: ["Academic Term: 2026-27"],
        timePeriod: "Current Term",
        calculationUsed: "Weighted composite health average across 7 domains",
        result: "Composite Health Index: 88/100 (GOOD)",
      },
      suggestedActions: [
        {
          label: "Executive Intelligence Dashboard",
          href: "/app/intelligence",
        },
        {
          label: "Active Operational Alerts",
          href: "/app/intelligence/alerts",
        },
      ],
      executionTimeMs: 400,
      toolName: "get_campus_metrics",
    };
  }
}

export const aiAssistantService = new AiAssistantService();
