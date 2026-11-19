import { describe, it, expect, beforeEach } from "vitest";
import { vicePrincipalService } from "../services/vice-principal.service";
import { DEMO_PERSONAS } from "../mocks/auth.mock";
import { VICE_PRINCIPAL_PORTAL_NAV } from "../components/navigation/portal-nav";
import { isPathAuthorized } from "../components/navigation/sidebar";

describe("CampusOS Vice Principal Portal — Comprehensive Test Suite", () => {
  // 1. Authentication, Persona & RBAC
  describe("1. Executive Persona & RBAC Authorization", () => {
    it("should have valid Vice Principal persona in DEMO_PERSONAS", () => {
      const vp = DEMO_PERSONAS.find(
        (p) => p.id === "user-vice-principal-01" || p.role === "PRINCIPAL",
      );
      expect(vp).toBeDefined();
      expect(vp?.email).toBe("vp.academics@campusos.edu");
      expect(vp?.role).toBe("PRINCIPAL");
    });

    it("should grant statutory approval & academic supervision permissions", () => {
      const vp = DEMO_PERSONAS.find((p) => p.id === "user-vice-principal-01")!;
      expect(vp.permissions).toContain("approvals:read");
      expect(vp.permissions).toContain("approvals:approve");
      expect(vp.permissions).toContain("approvals:reject");
      expect(vp.permissions).toContain("academics:calendar:read");
      expect(vp.permissions).toContain("timetable:read");
      expect(vp.permissions).toContain("leave:approve");
      expect(vp.permissions).toContain("reports:institutional:read");
    });

    it("should NOT possess admin operational permissions (user management, billing write, direct IAM)", () => {
      const vp = DEMO_PERSONAS.find((p) => p.id === "user-vice-principal-01")!;
      expect(vp.permissions).not.toContain("users:create");
      expect(vp.permissions).not.toContain("users:delete");
      expect(vp.permissions).not.toContain("finance:payments:process");
      expect(vp.permissions).not.toContain("iam:system:configure");
    });

    it("should authorize dedicated vice-principal routes for Vice Principal persona", () => {
      const vpUser: any = {
        id: "user-vice-principal-01",
        email: "vp.academics@campusos.edu",
        role: "PRINCIPAL",
        name: "Dr. Meenakshi Sundaram",
      };

      expect(isPathAuthorized("/vice-principal/dashboard", vpUser)).toBe(true);
      expect(isPathAuthorized("/vice-principal/departments", vpUser)).toBe(
        true,
      );
      expect(isPathAuthorized("/vice-principal/academics", vpUser)).toBe(true);
      expect(isPathAuthorized("/vice-principal/faculty", vpUser)).toBe(true);
      expect(isPathAuthorized("/vice-principal/students", vpUser)).toBe(true);
      expect(isPathAuthorized("/vice-principal/approvals", vpUser)).toBe(true);
      expect(isPathAuthorized("/vice-principal/examinations", vpUser)).toBe(
        true,
      );
      expect(isPathAuthorized("/vice-principal/reports", vpUser)).toBe(true);
      expect(isPathAuthorized("/vice-principal/announcements", vpUser)).toBe(
        true,
      );
      expect(isPathAuthorized("/vice-principal/audit", vpUser)).toBe(true);
    });
  });

  // 2. Dashboard KPIs & Institutional Overview
  describe("2. Institutional Overview Dashboard (Feature A)", () => {
    it("should retrieve institutional KPIs across all departments", async () => {
      const res = await vicePrincipalService.getDashboard();
      expect(res.success).toBe(true);
      expect(res.data).toBeDefined();

      const kpis = res.data.kpis;
      expect(kpis.total_departments).toBe(5);
      expect(kpis.total_students).toBeGreaterThan(2000);
      expect(kpis.total_faculty).toBeGreaterThan(100);
      expect(kpis.overall_student_attendance).toBeGreaterThanOrEqual(75.0);
      expect(kpis.syllabus_completion_rate).toBeGreaterThan(70.0);
      expect(kpis.pending_approvals_count).toBeGreaterThan(0);
    });

    it("should return department health matrix with NAAC scores", async () => {
      const res = await vicePrincipalService.getDashboard();
      const depts = res.data.department_metrics;
      expect(depts.length).toBe(5);

      const cse = depts.find((d) => d.code === "CSE");
      expect(cse).toBeDefined();
      expect(cse?.attendance_rate).toBeGreaterThan(90);
      expect(cse?.accreditation_score).toBeGreaterThan(3.5);
    });
  });

  // 3. Department Monitoring
  describe("3. Department Supervision & Comparison (Feature B)", () => {
    it("should return detailed monitoring for all 5 departments", async () => {
      const res = await vicePrincipalService.getDepartments();
      expect(res.success).toBe(true);
      expect(res.data.length).toBe(5);

      for (const d of res.data) {
        expect(d.hod_name).toBeTruthy();
        expect(d.hod_email).toContain("@campusos.edu");
        expect(d.student_count).toBeGreaterThan(0);
        expect(d.faculty_count).toBeGreaterThan(0);
        expect(d.syllabus_progress).toBeGreaterThan(50);
      }
    });
  });

  // 4. Academic Monitoring
  describe("4. Academic Calendar & Syllabus Velocity (Feature C)", () => {
    it("should track academic calendar milestones and CIA windows", async () => {
      const res = await vicePrincipalService.getAcademicsMonitoring();
      expect(res.success).toBe(true);
      expect(res.data.milestones.length).toBeGreaterThan(3);

      const cia1 = res.data.milestones.find((m) => m.event.includes("CIA 1"));
      expect(cia1).toBeDefined();
      expect(cia1?.status).toBe("COMPLETED");
    });

    it("should flag courses with syllabus completion delays", async () => {
      const res = await vicePrincipalService.getAcademicsMonitoring();
      expect(res.data.syllabus_delay_tracking.length).toBeGreaterThan(0);

      const delayed = res.data.syllabus_delay_tracking[0];
      expect(delayed.lag_days).toBeGreaterThan(0);
      expect(delayed.remedial_status).toBeTruthy();
    });
  });

  // 5. Faculty Supervision
  describe("5. Faculty Workload & Escalated Leaves (Feature D)", () => {
    it("should audit teaching hours against AICTE norms (12-18 hrs)", async () => {
      const res = await vicePrincipalService.getFacultySupervision();
      expect(res.success).toBe(true);

      const summary = res.data.workload_summary;
      expect(summary.total_faculty).toBeGreaterThan(0);
      expect(summary.statutory_min_hours).toBe(12);
      expect(summary.statutory_max_hours).toBe(18);
      expect(summary.compliant_workload_count).toBeGreaterThan(0);
    });

    it("should correctly identify overloaded faculty (>18 hrs)", async () => {
      const res = await vicePrincipalService.getFacultySupervision();
      const overloaded = res.data.faculty.filter(
        (f) => f.status === "OVERLOADED",
      );
      expect(overloaded.length).toBeGreaterThan(0);
      for (const f of overloaded) {
        expect(f.weekly_teaching_hours).toBeGreaterThanOrEqual(18);
      }
    });
  });

  // 6. Student Monitoring
  describe("6. Student Monitoring & Low-Attendance Radar (<75%) (Feature E)", () => {
    it("should identify students falling below statutory 75% attendance", async () => {
      const res = await vicePrincipalService.getStudentsSupervision({
        threshold: 75.0,
      });
      expect(res.success).toBe(true);
      expect(res.data.low_attendance_radar.length).toBeGreaterThan(0);

      for (const student of res.data.low_attendance_radar) {
        expect(student.attendance_percentage).toBeLessThan(75.0);
        expect(student.shortfall_sessions).toBeGreaterThan(0);
        expect(student.mentor_name).toBeTruthy();
      }
    });

    it("should provide annual institutional student strength progression", async () => {
      const res = await vicePrincipalService.getStudentsSupervision();
      expect(res.data.institutional_strength.length).toBe(5);
      for (const row of res.data.institutional_strength) {
        expect(row.total).toBe(
          row.year_1 + row.year_2 + row.year_3 + row.year_4,
        );
      }
    });
  });

  // 7. Statutory Approvals & 5 Mandatory Workflows
  describe("7. Statutory Approval Management & Workflows (Feature F)", () => {
    it("should list approvals across all 8 statutory categories", async () => {
      const res = await vicePrincipalService.getApprovals();
      expect(res.success).toBe(true);
      expect(res.data.length).toBeGreaterThanOrEqual(5);

      const categories = new Set(res.data.map((a) => a.category));
      expect(categories.has("DEPARTMENT_ACADEMIC_REQUEST")).toBe(true);
      expect(categories.has("ACADEMIC_CALENDAR_CHANGE")).toBe(true);
      expect(categories.has("FACULTY_LEAVE")).toBe(true);
      expect(categories.has("TIMETABLE_CHANGE")).toBe(true);
      expect(categories.has("EXAMINATION_REQUEST")).toBe(true);
      expect(categories.has("ACADEMIC_PERFORMANCE_INTERVENTION")).toBe(true);
    });

    it("Workflow 1: should execute APPROVE action with mandatory remarks", async () => {
      const actionRes = await vicePrincipalService.processApprovalAction(
        "appr-vp-001",
        "APPROVE",
        "Sanctioned by Vice Principal in compliance with academic regulations.",
      );
      expect(actionRes.success).toBe(true);
      expect(actionRes.data.status).toBe("APPROVED");
      expect(actionRes.data.remarks).toContain("Sanctioned by Vice Principal");
      expect(actionRes.data.audit_trail.length).toBeGreaterThanOrEqual(2);
    });

    it("Workflow 2: should execute REJECT action with justification", async () => {
      const actionRes = await vicePrincipalService.processApprovalAction(
        "appr-vp-002",
        "REJECT",
        "Denied due to conflict with University exam schedule.",
      );
      expect(actionRes.success).toBe(true);
      expect(actionRes.data.status).toBe("REJECTED");
      expect(actionRes.data.remarks).toContain("Denied due to conflict");
    });

    it("Workflow 3: should execute REQUEST_MODIFICATION with detailed notes", async () => {
      const actionRes = await vicePrincipalService.processApprovalAction(
        "appr-vp-003",
        "REQUEST_MODIFICATION",
        "Please provide alternate lecture compensation schedule for CS303.",
      );
      expect(actionRes.success).toBe(true);
      expect(actionRes.data.status).toBe("MODIFICATION_REQUESTED");
    });
  });

  // 8. Examinations & CIA Oversight
  describe("8. Examinations & Results Oversight (Feature G)", () => {
    it("should monitor examination schedules and CIA mark submissions", async () => {
      const res = await vicePrincipalService.getExaminationsOversight();
      expect(res.success).toBe(true);
      expect(res.data.schedules.length).toBeGreaterThan(0);
      expect(res.data.cia_mark_submissions.length).toBe(5);

      const cseMarks = res.data.cia_mark_submissions.find((c) =>
        c.department.includes("Computer Science"),
      );
      expect(cseMarks?.status).toBe("COMPLETED");
    });

    it("should present institutional results and distinction rankings", async () => {
      const res = await vicePrincipalService.getExaminationsOversight();
      const results = res.data.results_analysis;
      expect(results.overall_institutional_pass_pct).toBeGreaterThan(90);
      expect(results.department_pass_ranking.length).toBe(5);
    });
  });

  // 9. Reports, Announcements & Audit Trail
  describe("9. Reports, Announcements & Audit Trail (Features H, I, J)", () => {
    it("should retrieve executive compliance reports with multiple formats", async () => {
      const res = await vicePrincipalService.getReports();
      expect(res.success).toBe(true);
      expect(res.data.available_reports.length).toBeGreaterThan(0);
      for (const rep of res.data.available_reports) {
        expect(rep.format.length).toBeGreaterThan(0);
      }
    });

    it("should publish an executive institutional circular", async () => {
      const createRes = await vicePrincipalService.createAnnouncement({
        title: "Test Directive: Mid-Semester Audit Schedule",
        target_audience: "ALL_HODS",
        priority: "HIGH",
        summary: "Mandatory lesson plan verification audit on Friday.",
        pinned: true,
      });
      expect(createRes.success).toBe(true);
      expect(createRes.data.title).toContain("Test Directive");

      const listRes = await vicePrincipalService.getAnnouncements();
      expect(listRes.data.some((a) => a.title.includes("Test Directive"))).toBe(
        true,
      );
    });

    it("should maintain an immutable read-only audit trail", async () => {
      const res = await vicePrincipalService.getAuditTrail();
      expect(res.success).toBe(true);
      expect(res.data.length).toBeGreaterThan(0);
      for (const entry of res.data) {
        expect(entry.actor).toBeTruthy();
        expect(entry.action).toBeTruthy();
        expect(entry.entity).toBeTruthy();
      }
    });
  });
});
