/**
 * CampusOS Intelligence & AI Assistant Module — Comprehensive Test Suite
 * Validates domain contracts, pure arithmetic & rule calculators, conversational lifecycle,
 * structured response blocks, source provenance & explainability, cross-domain correlations,
 * AI tool registry, operational alerts & insights lifecycle, and role-based permissions.
 */

import {
  aiConversationsService,
  aiAssistantService,
  aiInsightsService,
  aiAlertsService,
  aiAnalyticsService,
  aiToolsService,
  aiActivityService,
  aiSavedService,
  intelligenceService,
  calculateAttendanceRisk,
  calculateAcademicRisk,
  calculateFinanceRisk,
  calculatePlacementActivity,
  calculateCampusEngagement,
  calculateInfrastructureRisk,
  calculateDocumentRisk,
  calculateStudentRiskSummary,
  calculateDepartmentHealth,
  calculateCampusHealth,
} from "../services";
import {
  IntelligenceDomain,
  AIResponseBlockType,
  InsightStatus,
  AlertStatus,
} from "@campusos/types";

interface TestResult {
  testName: string;
  passed: boolean;
  message?: string;
}

export async function runIntelligenceModuleTests(): Promise<{
  passed: number;
  failed: number;
  results: TestResult[];
}> {
  const results: TestResult[] = [];

  function assert(condition: boolean, testName: string, failureMsg?: string) {
    if (condition) {
      results.push({ testName, passed: true });
    } else {
      results.push({
        testName,
        passed: false,
        message: failureMsg || "Assertion evaluated to false",
      });
    }
  }

  try {
    // ==========================================
    // 1. Intelligence Overview & Telemetry
    // ==========================================
    const overviewRes = await intelligenceService.getOverviewSummary();
    assert(
      overviewRes.success === true,
      "1. getOverviewSummary returns success",
    );
    assert(overviewRes.data.activeInsights >= 3, "1. Active insights tracked");
    assert(overviewRes.data.criticalAlerts >= 1, "1. Critical alerts tracked");
    assert(
      overviewRes.data.studentsRequiringAttention > 0,
      "1. Risk cohort tracked",
    );
    assert(
      overviewRes.data.totalQueriesRun > 1000,
      "1. Cumulative queries tracked",
    );

    const domainSummaries = overviewRes.data.domainSummaries;
    assert(
      Boolean(domainSummaries["Academics"]),
      "1. Academics domain health present",
    );
    assert(
      Boolean(domainSummaries["Attendance"]),
      "1. Attendance domain health present",
    );
    assert(
      Boolean(domainSummaries["Finance"]),
      "1. Finance domain health present",
    );
    assert(
      Boolean(domainSummaries["Placement"]),
      "1. Placement domain health present",
    );
    assert(
      Boolean(domainSummaries["Infrastructure"]),
      "1. Infrastructure domain health present",
    );
    assert(
      Boolean(domainSummaries["Documents"]),
      "1. Documents domain health present",
    );

    const healthMetricsRes = await intelligenceService.getCampusHealthMetrics();
    assert(
      healthMetricsRes.success === true,
      "1. getCampusHealthMetrics returns success",
    );
    assert(
      healthMetricsRes.data.length >= 8,
      "1. All 8 canonical domain health metrics loaded",
    );

    // ==========================================
    // 2. Pure Intelligence Calculators
    // ==========================================
    // Attendance Risk
    assert(
      calculateAttendanceRisk(88) === "LOW",
      "2. calculateAttendanceRisk(88%) = LOW",
    );
    assert(
      calculateAttendanceRisk(78) === "MEDIUM",
      "2. calculateAttendanceRisk(78%) = MEDIUM",
    );
    assert(
      calculateAttendanceRisk(65) === "HIGH",
      "2. calculateAttendanceRisk(65%) = HIGH",
    );
    assert(
      calculateAttendanceRisk(55) === "CRITICAL",
      "2. calculateAttendanceRisk(55%) = CRITICAL",
    );

    // Academic Risk
    assert(
      calculateAcademicRisk(8.5, 0) === "LOW",
      "2. calculateAcademicRisk(8.5 CGPA, 0 backlogs) = LOW",
    );
    assert(
      calculateAcademicRisk(7.0, 1) === "MEDIUM",
      "2. calculateAcademicRisk(7.0 CGPA, 1 backlog) = MEDIUM",
    );
    assert(
      calculateAcademicRisk(5.5, 2) === "HIGH",
      "2. calculateAcademicRisk(5.5 CGPA, 2 backlogs) = HIGH",
    );
    assert(
      calculateAcademicRisk(4.2, 3) === "CRITICAL",
      "2. calculateAcademicRisk(4.2 CGPA, 3 backlogs) = CRITICAL",
    );

    // Finance Risk
    assert(
      calculateFinanceRisk(0, 0) === "CLEAR",
      "2. calculateFinanceRisk(0 bal) = CLEAR",
    );
    assert(
      calculateFinanceRisk(15000, 15) === "LOW",
      "2. calculateFinanceRisk(15k bal, 15d) = LOW",
    );
    assert(
      calculateFinanceRisk(30000, 45) === "MEDIUM",
      "2. calculateFinanceRisk(30k bal, 45d) = MEDIUM",
    );
    assert(
      calculateFinanceRisk(65000, 75) === "HIGH",
      "2. calculateFinanceRisk(65k bal, 75d) = HIGH",
    );

    // Placement Funnel Activity
    const placementCalc = calculatePlacementActivity(100, 80, 40, 20);
    assert(
      placementCalc.placementRate === 20,
      "2. calculatePlacementActivity placement rate = 20%",
    );
    assert(
      placementCalc.shortlistRate === 50,
      "2. calculatePlacementActivity shortlist rate = 50%",
    );
    assert(
      placementCalc.applicationRate === 80,
      "2. calculatePlacementActivity application rate = 80%",
    );

    // Campus Engagement
    assert(
      calculateCampusEngagement(0, 0) === "LOW",
      "2. calculateCampusEngagement(0,0) = LOW",
    );
    assert(
      calculateCampusEngagement(1, 1) === "MODERATE",
      "2. calculateCampusEngagement(1,1) = MODERATE",
    );
    assert(
      calculateCampusEngagement(2, 1) === "HIGH",
      "2. calculateCampusEngagement(2,1) = HIGH",
    );
    assert(
      calculateCampusEngagement(3, 2) === "VERY_HIGH",
      "2. calculateCampusEngagement(3,2) = VERY_HIGH",
    );

    // Infrastructure Risk
    const infraRisk = calculateInfrastructureRisk(96, 8, 4);
    assert(
      infraRisk.status === "ELEVATED" || infraRisk.status === "CRITICAL",
      "2. calculateInfrastructureRisk detects elevated load",
    );

    // Document Compliance Risk
    assert(
      calculateDocumentRisk(0, 0) === "LOW",
      "2. calculateDocumentRisk(0,0) = LOW",
    );
    assert(
      calculateDocumentRisk(1, 0) === "MEDIUM",
      "2. calculateDocumentRisk(1,0) = MEDIUM",
    );
    assert(
      calculateDocumentRisk(3, 0) === "HIGH",
      "2. calculateDocumentRisk(3,0) = HIGH",
    );

    // Holistic Student Risk Summary
    const studentRisk = calculateStudentRiskSummary({
      attendancePercentage: 55,
      cgpa: 5.2,
      failedSubjectsCount: 2,
      financeStatus: "OVERDUE",
      missingDocumentsCount: 1,
    });
    assert(
      studentRisk.compositeScore >= 60,
      "2. calculateStudentRiskSummary flags critical composite score",
    );
    assert(
      studentRisk.recommendedUrgency === "IMMEDIATE",
      "2. Recommended urgency is IMMEDIATE",
    );

    // Department Health Index
    const deptHealth = calculateDepartmentHealth({
      avgAttendance: 85,
      placementRate: 88,
      feeCollectionRate: 92,
      documentCompletionRate: 95,
    });
    assert(
      deptHealth.score >= 80,
      "2. calculateDepartmentHealth computes composite score",
    );
    assert(
      deptHealth.status === "EXCELLENT" || deptHealth.status === "GOOD",
      "2. Department status computed",
    );

    // Overall Campus Health
    const campusHealthCalc = calculateCampusHealth([
      {
        domain: IntelligenceDomain.ACADEMICS,
        label: "Acad",
        currentValue: 90,
        targetValue: 85,
        trend: "up",
        trendDescription: "ok",
        alertCount: 0,
        healthScore: 90,
        status: "EXCELLENT",
      },
      {
        domain: IntelligenceDomain.ATTENDANCE,
        label: "Att",
        currentValue: 85,
        targetValue: 85,
        trend: "up",
        trendDescription: "ok",
        alertCount: 1,
        healthScore: 85,
        status: "GOOD",
      },
    ]);
    assert(
      campusHealthCalc.overallScore > 0,
      "2. calculateCampusHealth computes overall score",
    );
    assert(
      campusHealthCalc.status === "EXCELLENT" ||
        campusHealthCalc.status === "GOOD",
      "2. Overall status computed",
    );

    // ==========================================
    // 3. AI Assistant & Conversational Engine
    // ==========================================
    // Preset Prompts
    const adminPrompts = aiAssistantService.getSuggestedPrompts("SUPER_ADMIN");
    assert(adminPrompts.length >= 5, "3. Admin preset prompts provided");
    const studentPrompts = aiAssistantService.getSuggestedPrompts("STUDENT");
    assert(
      studentPrompts.length >= 4,
      "3. Student persona preset prompts provided",
    );

    // Create Conversation
    const newConvRes = await aiConversationsService.createConversation({
      title: "Test Academic Query",
      domain: IntelligenceDomain.ACADEMICS,
    });
    assert(
      newConvRes.success === true,
      "3. createConversation returns success",
    );
    assert(
      Boolean(newConvRes.data.id),
      "3. Conversation assigned canonical ID",
    );

    // Rename Conversation
    const renameRes = await aiConversationsService.renameConversation(
      newConvRes.data.id,
      "Renamed Query",
    );
    assert(
      renameRes.success === true && renameRes.data?.title === "Renamed Query",
      "3. renameConversation modifies title",
    );

    // Pin Conversation
    const pinRes = await aiConversationsService.togglePinConversation(
      newConvRes.data.id,
    );
    assert(
      pinRes.success === true && pinRes.data?.isPinned === true,
      "3. togglePinConversation pins conversation",
    );

    // Send Attendance Query
    const attQueryRes = await aiAssistantService.sendQuery({
      query: "Which students have attendance below 75%?",
      domain: IntelligenceDomain.ATTENDANCE,
      conversationId: newConvRes.data.id,
    });
    assert(
      attQueryRes.success === true,
      "3. sendQuery attendance returns success",
    );
    assert(
      attQueryRes.data.blocks.length >= 2,
      "3. Structured response blocks generated",
    );
    assert(
      attQueryRes.data.sources.length >= 1,
      "3. Contextual data sources linked",
    );
    assert(
      Boolean(attQueryRes.data.explainability),
      "3. Methodology and explainability provided",
    );
    assert(
      attQueryRes.data.explainability.dataSources.length > 0,
      "3. Explainability specifies underlying data tables",
    );

    // Send Cross-Domain Query (Attendance + Fees)
    const crossQueryRes = await aiAssistantService.sendQuery({
      query: "Which students have low attendance and outstanding fees?",
      domain: IntelligenceDomain.ALL,
    });
    assert(
      crossQueryRes.success === true,
      "3. Cross-domain query (attendance + fees) succeeds",
    );
    assert(
      crossQueryRes.data.reply.includes("Vikram Aditya") ||
        crossQueryRes.data.reply.includes("cross-domain") ||
        crossQueryRes.data.blocks.length > 0,
      "3. Cross-domain identified students",
    );

    // Send Cross-Domain Query (Placement + Documents)
    const placeDocQueryRes = await aiAssistantService.sendQuery({
      query:
        "Which students are eligible for placement but have missing documents?",
      domain: IntelligenceDomain.PLACEMENT,
    });
    assert(
      placeDocQueryRes.success === true,
      "3. Cross-domain query (placement + documents) succeeds",
    );

    // Student Permission Enforcement
    const studentRestrictedQuery = await aiAssistantService.sendQuery({
      query: "Show institution revenue and salary by department",
      domain: IntelligenceDomain.FINANCE,
      context: { role: "STUDENT" },
    });
    assert(
      studentRestrictedQuery.success === true,
      "3. Student restricted query intercepted gracefully",
    );
    assert(
      studentRestrictedQuery.data.reply.includes("Permission Restricted") ||
        studentRestrictedQuery.data.blocks.some(
          (b) => b.type === AIResponseBlockType.WARNING,
        ),
      "3. Permission restricted warning rendered for student",
    );

    // ==========================================
    // 4. Intelligence Insights Lifecycle
    // ==========================================
    const insightsRes = await aiInsightsService.listInsights();
    assert(insightsRes.success === true, "4. listInsights returns success");
    assert(insightsRes.data.length >= 3, "4. Seed insights catalog loaded");

    const testInsight = insightsRes.data[0];
    const insightDetail = await aiInsightsService.getInsightById(
      testInsight.id,
    );
    assert(
      insightDetail.success === true &&
        insightDetail.data?.id === testInsight.id,
      "4. getInsightById returns full profile",
    );

    // Save Insight
    const saveInsRes = await aiInsightsService.toggleSaveInsight(
      testInsight.id,
    );
    assert(saveInsRes.success === true, "4. toggleSaveInsight toggles state");

    // Update Status
    const reviewInsRes = await aiInsightsService.markInsightReviewed(
      testInsight.id,
      "Dr. S. Ramanathan",
    );
    assert(
      reviewInsRes.success === true &&
        reviewInsRes.data?.status === InsightStatus.REVIEWED,
      "4. markInsightReviewed updates status",
    );

    const actionInsRes = await aiInsightsService.markInsightActioned(
      testInsight.id,
      "Dr. S. Ramanathan",
    );
    assert(
      actionInsRes.success === true &&
        actionInsRes.data?.status === InsightStatus.ACTIONED,
      "4. markInsightActioned updates status",
    );

    // ==========================================
    // 5. Operational Alerts Lifecycle
    // ==========================================
    const alertsRes = await aiAlertsService.listAlerts();
    assert(alertsRes.success === true, "5. listAlerts returns success");
    assert(alertsRes.data.length >= 3, "5. Seed alerts catalog loaded");

    const testAlert = alertsRes.data[0];
    const alertDetail = await aiAlertsService.getAlertById(testAlert.id);
    assert(
      alertDetail.success === true && alertDetail.data?.id === testAlert.id,
      "5. getAlertById returns full profile",
    );

    // Acknowledge Alert
    const ackRes = await aiAlertsService.acknowledgeAlert(
      testAlert.id,
      "Admin User",
    );
    assert(
      ackRes.success === true &&
        ackRes.data?.status === AlertStatus.ACKNOWLEDGED,
      "5. acknowledgeAlert updates status",
    );
    assert(
      Boolean(ackRes.data?.acknowledgedAt),
      "5. Acknowledged timestamp recorded",
    );

    // Resolve Alert
    const resAlertRes = await aiAlertsService.resolveAlert(
      testAlert.id,
      "Admin User",
      "Investigated and fixed",
    );
    assert(
      resAlertRes.success === true &&
        resAlertRes.data?.status === AlertStatus.RESOLVED,
      "5. resolveAlert updates status",
    );

    // ==========================================
    // 6. Analytics Builder Execution
    // ==========================================
    const attAnalyticsRes = await aiAnalyticsService.runAnalyticsQuery({
      domain: IntelligenceDomain.ATTENDANCE,
      metric: "Average Attendance",
      dimension: "Department",
      timeRange: "Current Semester",
    });
    assert(
      attAnalyticsRes.success === true,
      "6. runAnalyticsQuery (Attendance) returns success",
    );
    assert(
      attAnalyticsRes.data.datasets.length > 0,
      "6. Attendance analytics returns datasets",
    );
    assert(
      Boolean(attAnalyticsRes.data.tableData),
      "6. Attendance analytics includes tabular data",
    );

    const finAnalyticsRes = await aiAnalyticsService.runAnalyticsQuery({
      domain: IntelligenceDomain.FINANCE,
      metric: "Billed vs Realized",
      dimension: "Fee Head",
      timeRange: "Current Semester",
    });
    assert(
      finAnalyticsRes.success === true,
      "6. runAnalyticsQuery (Finance) returns success",
    );

    // ==========================================
    // 7. AI Tool Registry & Activity Audit
    // ==========================================
    const toolsRes = await aiToolsService.listAITools();
    assert(toolsRes.success === true, "7. listAITools returns success");
    assert(
      toolsRes.data.length >= 14,
      "7. All 14 required enterprise tools registered",
    );

    const studentProfileTool = await aiToolsService.getAITool(
      "get_student_profile",
    );
    assert(
      Boolean(studentProfileTool.data),
      "7. get_student_profile tool exists in registry",
    );

    const attendanceTool = await aiToolsService.getAITool(
      "get_attendance_summary",
    );
    assert(
      Boolean(attendanceTool.data),
      "7. get_attendance_summary tool exists in registry",
    );

    const actLogRes = await aiActivityService.listAIActivity();
    assert(
      actLogRes.success === true,
      "7. listAIActivity returns audit ledger",
    );
    assert(actLogRes.data.length > 0, "7. Activity audit records present");

    // ==========================================
    // 8. Saved Insights Management
    // ==========================================
    const saveNewRes = await aiSavedService.saveItem({
      title: "Test Saved Insight View",
      type: "INSIGHT",
      domain: IntelligenceDomain.ATTENDANCE,
      ownerName: "Administrator",
      ownerRole: "SUPER_ADMIN",
      contentSnippet: "Test summary of attendance audit",
      href: "/app/intelligence/insights/ins-001",
    });
    assert(saveNewRes.success === true, "8. saveItem adds new bookmark");

    const savedListRes = await aiSavedService.listSavedInsights();
    assert(
      savedListRes.success === true,
      "8. listSavedInsights returns success",
    );
    assert(
      savedListRes.data.some((s) => s.id === saveNewRes.data.id),
      "8. Newly saved item present in list",
    );

    const removeSavedRes = await aiSavedService.removeSavedInsight(
      saveNewRes.data.id,
    );
    assert(
      removeSavedRes.success === true,
      "8. removeSavedInsight deletes bookmark",
    );

    // ==========================================
    // 9. Contextual Intelligence (Student 360)
    // ==========================================
    const studentProfileRes =
      await intelligenceService.getStudentIntelligenceProfile("stu-001");
    assert(
      studentProfileRes.success === true,
      "9. getStudentIntelligenceProfile returns success",
    );
    assert(
      studentProfileRes.data?.studentName === "Aarav Patel",
      "9. Profile corresponds to Aarav Patel",
    );
    assert(
      Boolean(studentProfileRes.data?.attendanceRisk),
      "9. Profile provides attendance risk assessment",
    );
    assert(
      (studentProfileRes.data?.recommendedActions?.length ?? 0) > 0,
      "9. Operational interventions recommended",
    );

    // Department Health
    const deptHealthRes =
      await intelligenceService.getDepartmentHealth("dept-cse");
    assert(
      deptHealthRes.success === true && deptHealthRes.data.length > 0,
      "9. getDepartmentHealth returns CSE health summary",
    );
    assert(
      deptHealthRes.data[0].avgAttendance > 80,
      "9. Department average attendance computed",
    );
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    results.push({
      testName: "Global Execution Catch",
      passed: false,
      message: errorMsg,
    });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;

  return { passed, failed, results };
}

if (
  typeof process !== "undefined" &&
  process.argv[1]?.includes("intelligence-module.test")
) {
  runIntelligenceModuleTests().then((res) => {
    console.log(`\n======================================================`);
    console.log(`CampusOS Intelligence & AI Assistant Module Test Results:`);
    console.log(`Passed: ${res.passed}, Failed: ${res.failed}`);
    console.log(`======================================================`);
    res.results.forEach((r) => {
      console.log(
        `${r.passed ? "✔ PASS" : "✖ FAIL"}: ${r.testName}${r.message ? ` (${r.message})` : ""}`,
      );
    });
    if (res.failed > 0) {
      process.exit(1);
    }
  });
}
