import { ApiResponse } from "@campusos/types";
import { GlobalSearchResultItem } from "@/types/domain";
import { peopleService } from "./people.service";
import {
  MOCK_ACADEMIC_SUBJECTS,
  MOCK_CURRICULUM_SCHEMES,
  MOCK_COURSE_OFFERING_DETAILS,
} from "@/mocks/academics.mock";
import {
  MOCK_COMPANIES,
  MOCK_JOB_DRIVES,
  MOCK_POSITIONS,
  MOCK_APPLICATIONS,
  MOCK_OFFERS,
  MOCK_PLACEMENT_PROFILES,
} from "@/mocks/placement.mock";
import {
  MOCK_CANONICAL_INVOICES,
  MOCK_CANONICAL_FEE_STRUCTURES,
  MOCK_CANONICAL_PAYMENTS,
  MOCK_CANONICAL_RECEIPTS,
  MOCK_CANONICAL_SCHOLARSHIPS,
  MOCK_CANONICAL_REFUNDS,
} from "@/mocks/finance.mock";
import { MOCK_EVENTS } from "@/mocks/campus.mock";
import { MOCK_DOCUMENTS } from "@/mocks/documents.mock";
import { MOCK_CANONICAL_SESSIONS } from "@/mocks/attendance.mock";
import {
  MOCK_EXAMINATIONS,
  MOCK_CANONICAL_ASSESSMENTS,
  MOCK_CANONICAL_EXAM_SCHEDULES,
} from "@/mocks/examinations.mock";

class SearchService {
  async search(query: string): Promise<ApiResponse<GlobalSearchResultItem[]>> {
    if (!query || query.trim().length < 2) {
      return { success: true, data: [] };
    }

    const q = query.toLowerCase().trim();
    const results: GlobalSearchResultItem[] = [];

    // Query People Service
    const peopleRes = await peopleService.searchPeople(q);
    if (peopleRes.data) {
      peopleRes.data.forEach((p) => {
        const catMap: Record<string, "Student" | "Faculty" | "Staff"> = {
          STUDENT: "Student",
          FACULTY: "Faculty",
          STAFF: "Staff",
        };
        results.push({
          id: p.id,
          title: p.name,
          subtitle: `${p.code} • ${p.designationOrProgram} (${p.department})`,
          category: catMap[p.personType] || "Student",
          href: p.href,
          badge: p.status,
        });
      });
    }

    // Search Academic Subjects
    MOCK_ACADEMIC_SUBJECTS.forEach((sub) => {
      if (
        sub.name.toLowerCase().includes(q) ||
        sub.code.toLowerCase().includes(q) ||
        sub.departmentName.toLowerCase().includes(q)
      ) {
        results.push({
          id: sub.id,
          title: `${sub.code} — ${sub.name}`,
          subtitle: `${sub.departmentName} • ${sub.credits} Credits (${sub.type})`,
          category: "Course",
          href: `/app/academics/subjects/${sub.id}`,
          badge: sub.status,
        });
      }
    });

    // Search Curricula Schemes
    MOCK_CURRICULUM_SCHEMES.forEach((curr) => {
      if (
        curr.programName.toLowerCase().includes(q) ||
        curr.regulation.toLowerCase().includes(q) ||
        curr.department.toLowerCase().includes(q)
      ) {
        results.push({
          id: curr.id,
          title: `${curr.programName} (${curr.regulation})`,
          subtitle: `${curr.version} • ${curr.totalCredits} Cr • ${curr.department}`,
          category: "Curriculum",
          href: `/app/academics/curricula/${curr.id}`,
          badge: curr.status,
        });
      }
    });

    // Search Course Offerings
    MOCK_COURSE_OFFERING_DETAILS.forEach((off) => {
      if (
        off.subjectCode.toLowerCase().includes(q) ||
        off.subjectName.toLowerCase().includes(q) ||
        off.section.toLowerCase().includes(q) ||
        `section ${off.section}`.toLowerCase().includes(q) ||
        off.programName.toLowerCase().includes(q)
      ) {
        results.push({
          id: off.id,
          title: `${off.subjectCode}: Section ${off.section}`,
          subtitle: `${off.subjectName} • Sem ${off.semester} (AY ${off.academicYear})`,
          category: "Offering",
          href: `/app/academics/course-offerings/${off.id}`,
          badge: off.status,
        });
      }
    });

    // Search Attendance Hub & Sessions
    if ("attendance".includes(q) || "today's sessions".includes(q) || "sessions".includes(q)) {
      results.push({
        id: "nav-att-overview",
        title: "Attendance Operations Hub",
        subtitle: "Real-time registers, course attendance analytics, leave approvals",
        category: "Attendance",
        href: "/app/attendance",
      });
    }
    if ("attendance reports".includes(q) || "reports".includes(q)) {
      results.push({
        id: "nav-att-reports",
        title: "Attendance Reports & Compliance",
        subtitle: "Student rosters, shortage lists, condonation audits",
        category: "Attendance",
        href: "/app/attendance/reports",
      });
    }
    if ("low attendance".includes(q) || "shortage".includes(q) || "risk".includes(q)) {
      results.push({
        id: "nav-att-shortage",
        title: "Low Attendance Risk Roster",
        subtitle: "Students below 75% requirement with recovery projections",
        category: "Attendance",
        href: "/app/attendance/students",
        badge: "ALERT",
      });
    }
    if ("leave requests".includes(q) || "leave".includes(q)) {
      results.push({
        id: "nav-att-leaves",
        title: "Student Leave Requests",
        subtitle: "Medical, on-duty, and sports leave exemptions",
        category: "Attendance",
        href: "/app/attendance/leaves",
      });
    }
    if ("attendance corrections".includes(q) || "corrections".includes(q)) {
      results.push({
        id: "nav-att-corrections",
        title: "Attendance Corrections Workflow",
        subtitle: "Supervised revisions to locked class registers",
        category: "Attendance",
        href: "/app/attendance/corrections",
      });
    }

    MOCK_CANONICAL_SESSIONS.forEach((sess) => {
      if (
        sess.courseCode.toLowerCase().includes(q) ||
        sess.courseName.toLowerCase().includes(q) ||
        sess.section.toLowerCase().includes(q) ||
        sess.facultyName.toLowerCase().includes(q)
      ) {
        results.push({
          id: sess.id,
          title: `${sess.courseCode} Attendance: ${sess.section}`,
          subtitle: `${sess.facultyName} • ${sess.date} (${sess.startTime})`,
          category: "Attendance",
          href: `/app/attendance/sessions/${sess.id}`,
          badge: sess.status,
        });
      }
    });

    // Search Examination Hub & Modules
    if ("examinations".includes(q) || "exams".includes(q) || "assessment".includes(q)) {
      results.push({
        id: "nav-exam-overview",
        title: "Examination & Assessment Hub",
        subtitle: "Course evaluation schemes, timetable schedules, marks scoring",
        category: "Examination",
        href: "/app/examinations",
      });
    }
    if ("marks entry".includes(q) || "enter marks".includes(q) || "marks".includes(q)) {
      results.push({
        id: "nav-exam-marks",
        title: "Marks Entry & Grading Matrix",
        subtitle: "Class roster scoring, draft auto-saves, and locked finalization",
        category: "Examination",
        href: "/app/examinations/marks",
      });
    }
    if ("exam schedule".includes(q) || "exam timetable".includes(q) || "schedules".includes(q)) {
      results.push({
        id: "nav-exam-schedules",
        title: "Exam Schedules & Timetables",
        subtitle: "Conflict-free paper scheduling and invigilator hall allocations",
        category: "Examination",
        href: "/app/examinations/schedules",
      });
    }
    if ("exam eligibility".includes(q) || "eligibility".includes(q) || "debarment".includes(q)) {
      results.push({
        id: "nav-exam-eligibility",
        title: "Student Examination Eligibility",
        subtitle: "75% attendance gate and HOD medical condonation workflow",
        category: "Examination",
        href: "/app/examinations/eligibility",
      });
    }
    if ("results".includes(q) || "gpa".includes(q) || "grades".includes(q)) {
      results.push({
        id: "nav-exam-results",
        title: "Semester Examination Results",
        subtitle: "10-point CBCS grade points, weighted outcomes, and GPA",
        category: "Examination",
        href: "/app/examinations/results",
      });
    }
    if ("publications".includes(q) || "publish results".includes(q)) {
      results.push({
        id: "nav-exam-publications",
        title: "Result Publications Ledger",
        subtitle: "Deliberate batch release to public student portals",
        category: "Examination",
        href: "/app/examinations/publications",
      });
    }

    // Search Canonical Assessments
    MOCK_CANONICAL_ASSESSMENTS.forEach((asm) => {
      if (
        asm.name.toLowerCase().includes(q) ||
        asm.courseCode.toLowerCase().includes(q) ||
        asm.courseName.toLowerCase().includes(q) ||
        asm.facultyName.toLowerCase().includes(q)
      ) {
        results.push({
          id: asm.id,
          title: `${asm.courseCode}: ${asm.name}`,
          subtitle: `${asm.type} • Max: ${asm.maxMarks} • ${asm.facultyName} (Sec ${asm.section})`,
          category: "Assessment",
          href: `/app/examinations/assessments/${asm.id}`,
          badge: asm.status,
        });
      }
    });

    // Search Exam Timetables
    MOCK_CANONICAL_EXAM_SCHEDULES.forEach((sch) => {
      if (
        sch.courseCode.toLowerCase().includes(q) ||
        sch.courseName.toLowerCase().includes(q) ||
        sch.room.toLowerCase().includes(q) ||
        sch.facultyName.toLowerCase().includes(q)
      ) {
        results.push({
          id: sch.id,
          title: `Exam: ${sch.courseCode} (${sch.room})`,
          subtitle: `${sch.date} (${sch.startTime} - ${sch.endTime}) • Invigilator: ${sch.facultyName}`,
          category: "Examination",
          href: `/app/examinations/schedules/${sch.id}`,
          badge: sch.status,
        });
      }
    });

    // Placement Hub Navigation
    if ("placement".includes(q) || "career".includes(q) || "jobs".includes(q) || "hiring".includes(q)) {
      results.push({
        id: "nav-placement-hub",
        title: "Placement Operations Hub",
        subtitle: "Corporate partners, recruitment drives, candidate shortlisting & offers",
        category: "Placement",
        href: "/app/placement",
      });
    }

    // Search Placement Drives
    MOCK_JOB_DRIVES.forEach((d) => {
      if (
        d.title.toLowerCase().includes(q) ||
        d.companyName.toLowerCase().includes(q) ||
        d.code.toLowerCase().includes(q)
      ) {
        results.push({
          id: d.id,
          title: `${d.code} — ${d.title}`,
          subtitle: `${d.companyName} • ${d.driveType} • Deadline: ${d.applicationDeadline}`,
          category: "Drive",
          href: `/app/placement/drives/${d.id}`,
          badge: d.status,
        });
      }
    });

    // Search Companies / Corporate Partners
    MOCK_COMPANIES.forEach((c) => {
      if (
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        c.industry.toLowerCase().includes(q)
      ) {
        results.push({
          id: c.id,
          title: `${c.code} — ${c.name}`,
          subtitle: `${c.industry} • Avg CTC: ₹${c.averageCtcLpa} LPA (${c.tier})`,
          category: "Company",
          href: `/app/placement/companies/${c.id}`,
          badge: c.status,
        });
      }
    });

    // Search Positions
    MOCK_POSITIONS.forEach((pos) => {
      if (
        pos.title.toLowerCase().includes(q) ||
        pos.companyName.toLowerCase().includes(q) ||
        pos.departmentFunction.toLowerCase().includes(q)
      ) {
        results.push({
          id: pos.id,
          title: `${pos.title} — ${pos.companyName}`,
          subtitle: `₹${pos.ctcLpa} LPA • Min CGPA: ${pos.minCgpa} • ${pos.location}`,
          category: "Placement",
          href: `/app/placement/positions`,
          badge: pos.status,
        });
      }
    });

    // Search Applications
    MOCK_APPLICATIONS.forEach((app) => {
      if (
        app.applicationCode.toLowerCase().includes(q) ||
        app.studentName.toLowerCase().includes(q) ||
        app.companyName.toLowerCase().includes(q) ||
        app.positionTitle.toLowerCase().includes(q)
      ) {
        results.push({
          id: app.id,
          title: `${app.applicationCode} — ${app.studentName}`,
          subtitle: `${app.companyName} (${app.positionTitle}) • Stage: ${app.currentStage}`,
          category: "Application",
          href: `/app/placement/applications/${app.id}`,
          badge: app.status,
        });
      }
    });

    // Search Offers
    MOCK_OFFERS.forEach((ofr) => {
      if (
        ofr.offerCode.toLowerCase().includes(q) ||
        ofr.studentName.toLowerCase().includes(q) ||
        ofr.companyName.toLowerCase().includes(q)
      ) {
        results.push({
          id: ofr.id,
          title: `${ofr.offerCode} — ${ofr.studentName}`,
          subtitle: `${ofr.companyName} (${ofr.positionTitle}) • ₹${ofr.ctcLpa} LPA`,
          category: "Offer",
          href: `/app/placement/offers/${ofr.id}`,
          badge: ofr.status,
        });
      }
    });

    // Search Finance Hub & Submodules
    if ("finance".includes(q) || "fees".includes(q) || "billing".includes(q)) {
      results.push({
        id: "nav-fin-overview",
        title: "Finance & Billing Operations Hub",
        subtitle: "Fee schedules, student invoicing, payment records & revenue metrics",
        category: "Finance",
        href: "/app/finance",
      });
    }
    if ("fee structure".includes(q) || "fee schedule".includes(q)) {
      results.push({
        id: "nav-fin-structures",
        title: "Fee Structures Directory",
        subtitle: "Configured academic, lab, hostel & examination fee schedules",
        category: "Finance",
        href: "/app/finance/fee-structures",
      });
    }
    if ("fee categories".includes(q) || "category".includes(q)) {
      results.push({
        id: "nav-fin-categories",
        title: "Fee Categories & Heads",
        subtitle: "Tuition, examination, lab, library, hostel, and transport fee heads",
        category: "Finance",
        href: "/app/finance/fee-categories",
      });
    }
    if ("fee assignments".includes(q) || "assignments".includes(q)) {
      results.push({
        id: "nav-fin-assignments",
        title: "Student Fee Assignments",
        subtitle: "Link student cohorts to fee structures with scholarship deductions",
        category: "Finance",
        href: "/app/finance/assignments",
      });
    }
    if ("payments".includes(q) || "pay".includes(q) || "transactions".includes(q)) {
      results.push({
        id: "nav-fin-payments",
        title: "Payment Transactions Ledger",
        subtitle: "UPI, bank transfer, card, and cash payment audit entries",
        category: "Payment",
        href: "/app/finance/payments",
      });
    }
    if ("receipts".includes(q) || "receipt".includes(q)) {
      results.push({
        id: "nav-fin-receipts",
        title: "Fee Receipts Registry",
        subtitle: "Official electronic money receipts with print verification",
        category: "Receipt",
        href: "/app/finance/receipts",
      });
    }
    if ("scholarships".includes(q) || "concessions".includes(q) || "waiver".includes(q)) {
      results.push({
        id: "nav-fin-scholarships",
        title: "Scholarship & Fee Concession Schemes",
        subtitle: "Merit, fellowship, and need-based tuition assistance schemes",
        category: "Scholarship",
        href: "/app/finance/scholarships",
      });
    }
    if ("refunds".includes(q) || "refund".includes(q)) {
      results.push({
        id: "nav-fin-refunds",
        title: "Fee Refund Applications Ledger",
        subtitle: "Review, approve, and process student caution and fee reimbursements",
        category: "Finance",
        href: "/app/finance/refunds",
      });
    }

    // Search Invoices
    MOCK_CANONICAL_INVOICES.forEach((inv) => {
      if (
        inv.invoiceNumber.toLowerCase().includes(q) ||
        inv.studentName.toLowerCase().includes(q) ||
        inv.rollNumber.toLowerCase().includes(q)
      ) {
        results.push({
          id: inv.id,
          title: `${inv.invoiceNumber} — ${inv.studentName}`,
          subtitle: `₹${inv.netPayable.toLocaleString()} (Bal: ₹${inv.outstandingAmount.toLocaleString()}) • Due: ${inv.dueDate}`,
          category: "Invoice",
          href: `/app/finance/invoices/${inv.id}`,
          badge: inv.status,
        });
      }
    });

    // Search Fee Structures
    MOCK_CANONICAL_FEE_STRUCTURES.forEach((fs) => {
      if (
        fs.name.toLowerCase().includes(q) ||
        fs.code.toLowerCase().includes(q) ||
        fs.program.toLowerCase().includes(q)
      ) {
        results.push({
          id: fs.id,
          title: `${fs.code} — ${fs.name}`,
          subtitle: `${fs.program} (Sem ${fs.semester}) • Total: ₹${fs.grossTotal.toLocaleString()}`,
          category: "Finance",
          href: `/app/finance/fee-structures/${fs.id}`,
          badge: fs.status,
        });
      }
    });

    // Search Payments
    MOCK_CANONICAL_PAYMENTS.forEach((p) => {
      if (
        p.transactionRef.toLowerCase().includes(q) ||
        p.studentName.toLowerCase().includes(q) ||
        p.receiptNumber.toLowerCase().includes(q)
      ) {
        results.push({
          id: p.id,
          title: `${p.transactionRef} — ${p.studentName}`,
          subtitle: `₹${p.amount.toLocaleString()} via ${p.paymentMethod} (${p.receiptNumber})`,
          category: "Payment",
          href: `/app/finance/payments/${p.id}`,
          badge: p.status,
        });
      }
    });

    // Search Receipts
    MOCK_CANONICAL_RECEIPTS.forEach((r) => {
      if (
        r.receiptNumber.toLowerCase().includes(q) ||
        r.studentName.toLowerCase().includes(q) ||
        r.invoiceNumber.toLowerCase().includes(q)
      ) {
        results.push({
          id: r.id,
          title: `${r.receiptNumber} — ${r.studentName}`,
          subtitle: `₹${r.amount.toLocaleString()} • ${r.invoiceNumber} (${r.paymentMethod})`,
          category: "Receipt",
          href: `/app/finance/receipts/${r.id}`,
          badge: r.status,
        });
      }
    });

    // Search Scholarships
    MOCK_CANONICAL_SCHOLARSHIPS.forEach((s) => {
      if (
        s.name.toLowerCase().includes(q) ||
        s.code.toLowerCase().includes(q) ||
        s.type.toLowerCase().includes(q)
      ) {
        results.push({
          id: s.id,
          title: `${s.code} — ${s.name}`,
          subtitle: `${s.type} • ${s.discountType === "PERCENTAGE" ? `${s.value}%` : `₹${s.value.toLocaleString()}`} Concession`,
          category: "Scholarship",
          href: `/app/finance/scholarships/${s.id}`,
          badge: s.status,
        });
      }
    });

    // Search Refunds
    MOCK_CANONICAL_REFUNDS.forEach((ref) => {
      if (
        ref.refundNumber.toLowerCase().includes(q) ||
        ref.studentName.toLowerCase().includes(q) ||
        ref.reason.toLowerCase().includes(q)
      ) {
        results.push({
          id: ref.id,
          title: `${ref.refundNumber} — ${ref.studentName}`,
          subtitle: `₹${ref.requestedAmount.toLocaleString()} • ${ref.reason}`,
          category: "Finance",
          href: `/app/finance/refunds/${ref.id}`,
          badge: ref.status,
        });
      }
    });

    // Search Events
    MOCK_EVENTS.forEach((e) => {
      if (e.title.toLowerCase().includes(q) || e.venue.toLowerCase().includes(q)) {
        results.push({
          id: e.id,
          title: e.title,
          subtitle: `${e.venue} • Starts: ${e.startDate}`,
          category: "Event",
          href: `/app/events/${e.id}`,
        });
      }
    });

    // Search Documents
    MOCK_DOCUMENTS.forEach((doc) => {
      if (doc.name.toLowerCase().includes(q) || doc.ownerName.toLowerCase().includes(q)) {
        results.push({
          id: doc.id,
          title: doc.name,
          subtitle: `${doc.ownerName} • ${doc.category} (${doc.fileType})`,
          category: "Document",
          href: `/app/documents`,
        });
      }
    });

    return {
      success: true,
      data: results.slice(0, 15),
    };
  }
}

export const searchService = new SearchService();
