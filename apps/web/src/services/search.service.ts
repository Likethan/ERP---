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
import {
  MOCK_EVENTS,
  MOCK_CLUBS,
  MOCK_ANNOUNCEMENTS,
  MOCK_VENUES,
} from "@/mocks/campus.mock";
import {
  MOCK_DOCUMENTS,
  MOCK_DOCUMENT_CATEGORIES,
  MOCK_CERTIFICATE_REQUESTS,
  MOCK_ISSUED_CERTIFICATES,
  MOCK_INSTITUTIONAL_RECORDS,
} from "@/mocks/documents.mock";
import { MOCK_CANONICAL_SESSIONS } from "@/mocks/attendance.mock";
import {
  MOCK_EXAMINATIONS,
  MOCK_CANONICAL_ASSESSMENTS,
  MOCK_CANONICAL_EXAM_SCHEDULES,
} from "@/mocks/examinations.mock";
import {
  MOCK_HOSTELS,
  MOCK_HOSTEL_ROOMS,
  MOCK_HOSTEL_ALLOCATIONS,
  MOCK_HOSTEL_COMPLAINTS,
  MOCK_TRANSPORT_ROUTES,
  MOCK_TRANSPORT_STOPS,
  MOCK_TRANSPORT_VEHICLES,
  MOCK_TRANSPORT_DRIVERS,
  MOCK_FACILITIES,
  MOCK_MAINTENANCE_REQUESTS,
} from "@/mocks/infrastructure.mock";
import {
  MOCK_INSIGHTS,
  MOCK_ALERTS,
  MOCK_AI_TOOLS,
} from "@/mocks/intelligence-dataset.mock";

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
    if (
      "attendance".includes(q) ||
      "today's sessions".includes(q) ||
      "sessions".includes(q)
    ) {
      results.push({
        id: "nav-att-overview",
        title: "Attendance Operations Hub",
        subtitle:
          "Real-time registers, course attendance analytics, leave approvals",
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
    if (
      "low attendance".includes(q) ||
      "shortage".includes(q) ||
      "risk".includes(q)
    ) {
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
    if (
      "examinations".includes(q) ||
      "exams".includes(q) ||
      "assessment".includes(q)
    ) {
      results.push({
        id: "nav-exam-overview",
        title: "Examination & Assessment Hub",
        subtitle:
          "Course evaluation schemes, timetable schedules, marks scoring",
        category: "Examination",
        href: "/app/examinations",
      });
    }
    if (
      "marks entry".includes(q) ||
      "enter marks".includes(q) ||
      "marks".includes(q)
    ) {
      results.push({
        id: "nav-exam-marks",
        title: "Marks Entry & Grading Matrix",
        subtitle:
          "Class roster scoring, draft auto-saves, and locked finalization",
        category: "Examination",
        href: "/app/examinations/marks",
      });
    }
    if (
      "exam schedule".includes(q) ||
      "exam timetable".includes(q) ||
      "schedules".includes(q)
    ) {
      results.push({
        id: "nav-exam-schedules",
        title: "Exam Schedules & Timetables",
        subtitle:
          "Conflict-free paper scheduling and invigilator hall allocations",
        category: "Examination",
        href: "/app/examinations/schedules",
      });
    }
    if (
      "exam eligibility".includes(q) ||
      "eligibility".includes(q) ||
      "debarment".includes(q)
    ) {
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
    if (
      "placement".includes(q) ||
      "career".includes(q) ||
      "jobs".includes(q) ||
      "hiring".includes(q)
    ) {
      results.push({
        id: "nav-placement-hub",
        title: "Placement Operations Hub",
        subtitle:
          "Corporate partners, recruitment drives, candidate shortlisting & offers",
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
        subtitle:
          "Fee schedules, student invoicing, payment records & revenue metrics",
        category: "Finance",
        href: "/app/finance",
      });
    }
    if ("fee structure".includes(q) || "fee schedule".includes(q)) {
      results.push({
        id: "nav-fin-structures",
        title: "Fee Structures Directory",
        subtitle:
          "Configured academic, lab, hostel & examination fee schedules",
        category: "Finance",
        href: "/app/finance/fee-structures",
      });
    }
    if ("fee categories".includes(q) || "category".includes(q)) {
      results.push({
        id: "nav-fin-categories",
        title: "Fee Categories & Heads",
        subtitle:
          "Tuition, examination, lab, library, hostel, and transport fee heads",
        category: "Finance",
        href: "/app/finance/fee-categories",
      });
    }
    if ("fee assignments".includes(q) || "assignments".includes(q)) {
      results.push({
        id: "nav-fin-assignments",
        title: "Student Fee Assignments",
        subtitle:
          "Link student cohorts to fee structures with scholarship deductions",
        category: "Finance",
        href: "/app/finance/assignments",
      });
    }
    if (
      "payments".includes(q) ||
      "pay".includes(q) ||
      "transactions".includes(q)
    ) {
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
    if (
      "scholarships".includes(q) ||
      "concessions".includes(q) ||
      "waiver".includes(q)
    ) {
      results.push({
        id: "nav-fin-scholarships",
        title: "Scholarship & Fee Concession Schemes",
        subtitle:
          "Merit, fellowship, and need-based tuition assistance schemes",
        category: "Scholarship",
        href: "/app/finance/scholarships",
      });
    }
    if ("refunds".includes(q) || "refund".includes(q)) {
      results.push({
        id: "nav-fin-refunds",
        title: "Fee Refund Applications Ledger",
        subtitle:
          "Review, approve, and process student caution and fee reimbursements",
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

    // Search Campus Navigation
    if (
      "campus".includes(q) ||
      "campus hub".includes(q) ||
      "student engagement".includes(q)
    ) {
      results.push({
        id: "nav-campus-hub",
        title: "Campus Operations & Engagement Hub",
        subtitle:
          "Events, clubs directory, institutional communication, and calendar",
        category: "Campus",
        href: "/app/campus",
      });
    }
    if (
      "events".includes(q) ||
      "hackathon".includes(q) ||
      "workshop".includes(q)
    ) {
      results.push({
        id: "nav-campus-events",
        title: "Campus Events Management",
        subtitle:
          "Browse university events, hackathons, symposiums, and registrations",
        category: "Campus",
        href: "/app/campus/events",
      });
    }
    if (
      "clubs".includes(q) ||
      "societies".includes(q) ||
      "organizations".includes(q)
    ) {
      results.push({
        id: "nav-campus-clubs",
        title: "Clubs & Student Organizations",
        subtitle:
          "Explore student societies, leadership rosters, and memberships",
        category: "Campus",
        href: "/app/campus/clubs",
      });
    }
    if (
      "announcements".includes(q) ||
      "notices".includes(q) ||
      "circulars".includes(q)
    ) {
      results.push({
        id: "nav-campus-announcements",
        title: "Campus Announcements & Dispatches",
        subtitle:
          "Official circulars, exam notices, and institutional advisories",
        category: "Campus",
        href: "/app/campus/announcements",
      });
    }

    // Search Campus Events
    MOCK_EVENTS.forEach((e) => {
      if (
        e.title.toLowerCase().includes(q) ||
        e.venue.toLowerCase().includes(q) ||
        e.category.toLowerCase().includes(q) ||
        e.organizer.toLowerCase().includes(q)
      ) {
        results.push({
          id: e.id,
          title: e.title,
          subtitle: `${e.category} • ${e.venue} • Starts: ${e.startDate}`,
          category: "Event",
          href: `/app/campus/events/${e.id}`,
          badge: e.status,
        });
      }
    });

    // Search Campus Clubs
    MOCK_CLUBS.forEach((c) => {
      if (
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        c.category.toLowerCase().includes(q) ||
        c.studentLead.toLowerCase().includes(q) ||
        c.facultyCoordinator.toLowerCase().includes(q)
      ) {
        results.push({
          id: c.id,
          title: `${c.code} — ${c.name}`,
          subtitle: `${c.category} • Lead: ${c.studentLead} • ${c.membersCount} members`,
          category: "Club",
          href: `/app/campus/clubs/${c.id}`,
          badge: c.status,
        });
      }
    });

    // Search Announcements
    MOCK_ANNOUNCEMENTS.forEach((a) => {
      if (
        a.title.toLowerCase().includes(q) ||
        a.content.toLowerCase().includes(q) ||
        a.publisher.toLowerCase().includes(q) ||
        a.category.toLowerCase().includes(q)
      ) {
        results.push({
          id: a.id,
          title: a.title,
          subtitle: `${a.category} • By ${a.publisher} • Published: ${a.publishDate}`,
          category: "Announcement",
          href: `/app/campus/announcements/${a.id}`,
          badge: a.priority,
        });
      }
    });

    // Search Venues
    MOCK_VENUES.forEach((v) => {
      if (
        v.name.toLowerCase().includes(q) ||
        v.building.toLowerCase().includes(q) ||
        v.roomNumber.toLowerCase().includes(q)
      ) {
        results.push({
          id: v.id,
          title: v.name,
          subtitle: `${v.building} (${v.roomNumber}) • Capacity: ${v.capacity}`,
          category: "Infrastructure",
          href: `/app/campus/events`,
        });
      }
    });

    // Search Documents
    MOCK_DOCUMENTS.forEach((doc) => {
      if (
        doc.name.toLowerCase().includes(q) ||
        doc.ownerName.toLowerCase().includes(q)
      ) {
        results.push({
          id: doc.id,
          title: doc.name,
          subtitle: `${doc.ownerName} • ${doc.category} (${doc.fileType})`,
          category: "Document",
          href: `/app/documents`,
        });
      }
    });

    // Search Infrastructure — Hostels
    MOCK_HOSTELS.forEach((h) => {
      if (
        h.name.toLowerCase().includes(q) ||
        h.code.toLowerCase().includes(q) ||
        h.wardenName.toLowerCase().includes(q)
      ) {
        results.push({
          id: h.id,
          title: h.name,
          subtitle: `${h.code} • ${h.type} Hostel • Warden: ${h.wardenName}`,
          category: "Infrastructure",
          href: `/app/infrastructure/hostel/${h.id}`,
          badge: h.status,
        });
      }
    });

    // Search Rooms
    MOCK_HOSTEL_ROOMS.forEach((r) => {
      if (
        r.roomNumber.toLowerCase().includes(q) ||
        r.hostelName.toLowerCase().includes(q)
      ) {
        results.push({
          id: r.id,
          title: `Room ${r.roomNumber} (${r.hostelName})`,
          subtitle: `${r.blockName} • Floor ${r.floor} • ${r.roomType}`,
          category: "Infrastructure",
          href: `/app/infrastructure/hostel/rooms/${r.id}`,
          badge: r.status,
        });
      }
    });

    // Search Hostel Allocations
    MOCK_HOSTEL_ALLOCATIONS.forEach((a) => {
      if (
        a.studentName.toLowerCase().includes(q) ||
        a.registerNumber.toLowerCase().includes(q) ||
        a.roomNumber.toLowerCase().includes(q)
      ) {
        results.push({
          id: a.id,
          title: `${a.studentName} (${a.registerNumber})`,
          subtitle: `${a.hostelName} • Room ${a.roomNumber} ${a.bedNumber}`,
          category: "Infrastructure",
          href: `/app/infrastructure/hostel/allocations/${a.id}`,
          badge: a.status,
        });
      }
    });

    // Search Hostel Complaints
    MOCK_HOSTEL_COMPLAINTS.forEach((c) => {
      if (
        c.title.toLowerCase().includes(q) ||
        c.ticketNumber.toLowerCase().includes(q) ||
        c.studentName.toLowerCase().includes(q)
      ) {
        results.push({
          id: c.id,
          title: `${c.ticketNumber} — ${c.title}`,
          subtitle: `${c.category} • ${c.hostelName} Room ${c.roomNumber} • ${c.priority}`,
          category: "Infrastructure",
          href: `/app/infrastructure/hostel/complaints/${c.id}`,
          badge: c.status,
        });
      }
    });

    // Search Transport Routes
    MOCK_TRANSPORT_ROUTES.forEach((rt) => {
      if (
        rt.name.toLowerCase().includes(q) ||
        rt.routeCode.toLowerCase().includes(q) ||
        rt.startPoint.toLowerCase().includes(q) ||
        rt.endPoint.toLowerCase().includes(q)
      ) {
        results.push({
          id: rt.id,
          title: `${rt.routeCode}: ${rt.name}`,
          subtitle: `${rt.stopsCount} Stops • ${rt.allocatedStudents}/${rt.capacity} Students • Vehicle: ${rt.vehicleNumber || "Unassigned"}`,
          category: "Infrastructure",
          href: `/app/infrastructure/transport/routes/${rt.id}`,
          badge: rt.status,
        });
      }
    });

    // Search Transport Stops
    MOCK_TRANSPORT_STOPS.forEach((st) => {
      if (
        st.name.toLowerCase().includes(q) ||
        st.code.toLowerCase().includes(q) ||
        st.routeCode.toLowerCase().includes(q)
      ) {
        results.push({
          id: st.id,
          title: `${st.name} (${st.code})`,
          subtitle: `Route ${st.routeCode} • Pickup: ${st.pickupTime} • ${st.studentCount} Students`,
          category: "Infrastructure",
          href: `/app/infrastructure/transport/stops/${st.id}`,
        });
      }
    });

    // Search Transport Vehicles
    MOCK_TRANSPORT_VEHICLES.forEach((v) => {
      if (
        v.registrationNumber.toLowerCase().includes(q) ||
        v.vehicleNumber.toLowerCase().includes(q) ||
        v.makeModel.toLowerCase().includes(q)
      ) {
        results.push({
          id: v.id,
          title: `${v.vehicleNumber} — ${v.registrationNumber}`,
          subtitle: `${v.makeModel} • Capacity: ${v.capacity} • ${v.fuelType}`,
          category: "Infrastructure",
          href: `/app/infrastructure/transport/vehicles/${v.id}`,
          badge: v.status,
        });
      }
    });

    // Search Transport Drivers
    MOCK_TRANSPORT_DRIVERS.forEach((d) => {
      if (
        d.name.toLowerCase().includes(q) ||
        d.employeeId.toLowerCase().includes(q) ||
        d.licenseNumber.toLowerCase().includes(q)
      ) {
        results.push({
          id: d.id,
          title: `${d.name} (${d.employeeId})`,
          subtitle: `Driver • ${d.licenseType} • Route: ${d.assignedRouteCode || "Standby"}`,
          category: "Infrastructure",
          href: `/app/infrastructure/transport/drivers/${d.id}`,
          badge: d.status,
        });
      }
    });

    // Search Facilities
    MOCK_FACILITIES.forEach((f) => {
      if (
        f.name.toLowerCase().includes(q) ||
        f.code.toLowerCase().includes(q) ||
        f.building.toLowerCase().includes(q)
      ) {
        results.push({
          id: f.id,
          title: f.name,
          subtitle: `${f.code} • ${f.building} • Capacity: ${f.capacity}`,
          category: "Infrastructure",
          href: `/app/infrastructure/facilities/${f.id}`,
          badge: f.status,
        });
      }
    });

    // Search Maintenance Requests
    MOCK_MAINTENANCE_REQUESTS.forEach((m) => {
      if (
        m.title.toLowerCase().includes(q) ||
        m.workOrderNumber.toLowerCase().includes(q) ||
        m.assetOrFacilityName.toLowerCase().includes(q)
      ) {
        results.push({
          id: m.id,
          title: `${m.workOrderNumber}: ${m.title}`,
          subtitle: `${m.category} • ${m.assetOrFacilityName} (${m.location})`,
          category: "Infrastructure",
          href: `/app/infrastructure/maintenance/${m.id}`,
          badge: m.status,
        });
      }
    });

    // Search Documents
    MOCK_DOCUMENTS.forEach((doc) => {
      if (
        doc.name.toLowerCase().includes(q) ||
        doc.ownerName.toLowerCase().includes(q) ||
        (doc.ownerRollNumber &&
          doc.ownerRollNumber.toLowerCase().includes(q)) ||
        (doc.documentNumber && doc.documentNumber.toLowerCase().includes(q)) ||
        doc.category.toLowerCase().includes(q) ||
        doc.documentType.toLowerCase().includes(q)
      ) {
        results.push({
          id: doc.id,
          title: doc.name,
          subtitle: `${doc.ownerName} • ${doc.category} • ${doc.documentType}`,
          category: "Documents" as any,
          href: `/app/documents/${doc.id}`,
          badge: doc.status,
        });
      }
    });

    // Search Document Categories
    MOCK_DOCUMENT_CATEGORIES.forEach((cat) => {
      if (
        cat.name.toLowerCase().includes(q) ||
        cat.code.toLowerCase().includes(q) ||
        cat.description.toLowerCase().includes(q)
      ) {
        results.push({
          id: cat.id,
          title: `Category: ${cat.name} (${cat.code})`,
          subtitle: `${cat.applicableRoles.join(", ")} • ${cat.applicableDocumentTypes.length} Document Types`,
          category: "Documents" as any,
          href: `/app/documents/categories/${cat.id}`,
        });
      }
    });

    // Search Certificate Requests
    MOCK_CERTIFICATE_REQUESTS.forEach((req) => {
      if (
        req.requestId.toLowerCase().includes(q) ||
        req.studentName.toLowerCase().includes(q) ||
        req.rollNumber.toLowerCase().includes(q) ||
        req.templateName.toLowerCase().includes(q) ||
        req.purpose.toLowerCase().includes(q)
      ) {
        results.push({
          id: req.id,
          title: `Cert Request: ${req.requestId} (${req.studentName})`,
          subtitle: `${req.templateName} • ${req.purpose}`,
          category: "Documents" as any,
          href: `/app/documents/certificates/requests/${req.id}`,
          badge: req.status,
        });
      }
    });

    // Search Issued Certificates
    MOCK_ISSUED_CERTIFICATES.forEach((cert) => {
      if (
        cert.certificateNumber.toLowerCase().includes(q) ||
        cert.recipientName.toLowerCase().includes(q) ||
        cert.recipientRollNumber.toLowerCase().includes(q) ||
        cert.certificateType.toLowerCase().includes(q)
      ) {
        results.push({
          id: cert.id,
          title: `Credential: ${cert.certificateNumber}`,
          subtitle: `${cert.recipientName} (${cert.recipientRollNumber}) • ${cert.certificateType}`,
          category: "Documents" as any,
          href: `/app/documents/certificates`,
          badge: cert.status,
        });
      }
    });

    // Search Institutional Records
    MOCK_INSTITUTIONAL_RECORDS.forEach((rec) => {
      if (
        rec.recordName.toLowerCase().includes(q) ||
        rec.code.toLowerCase().includes(q) ||
        rec.category.toLowerCase().includes(q) ||
        rec.ownerDepartment.toLowerCase().includes(q) ||
        (rec.referenceNumber && rec.referenceNumber.toLowerCase().includes(q))
      ) {
        results.push({
          id: rec.id,
          title: `Institutional Record: ${rec.recordName}`,
          subtitle: `${rec.code} • ${rec.category} • ${rec.ownerDepartment}`,
          category: "Documents" as any,
          href: `/app/documents/institutional-records/${rec.id}`,
          badge: rec.confidentiality,
        });
      }
    });

    // Search Intelligence Insights
    MOCK_INSIGHTS.forEach((ins) => {
      if (
        ins.title.toLowerCase().includes(q) ||
        ins.summary.toLowerCase().includes(q) ||
        ins.domain.toLowerCase().includes(q) ||
        ins.recommendedAction.toLowerCase().includes(q)
      ) {
        results.push({
          id: ins.id,
          title: `AI Insight: ${ins.title}`,
          subtitle: `${ins.domain} • ${ins.summary.slice(0, 75)}...`,
          category: "Intelligence",
          href: `/app/intelligence/insights/${ins.id}`,
          badge: ins.priority,
        });
      }
    });

    // Search Operational Alerts
    MOCK_ALERTS.forEach((alt) => {
      if (
        alt.title.toLowerCase().includes(q) ||
        alt.reason.toLowerCase().includes(q) ||
        alt.sourceDomain.toLowerCase().includes(q)
      ) {
        results.push({
          id: alt.id,
          title: `Alert: ${alt.title}`,
          subtitle: `${alt.sourceDomain} • ${alt.reason.slice(0, 75)}...`,
          category: "Intelligence",
          href: `/app/intelligence/alerts/${alt.id}`,
          badge: alt.severity,
        });
      }
    });

    // Search AI Tools
    MOCK_AI_TOOLS.forEach((tool) => {
      if (
        tool.name.toLowerCase().includes(q) ||
        tool.description.toLowerCase().includes(q) ||
        tool.domain.toLowerCase().includes(q)
      ) {
        results.push({
          id: tool.name,
          title: `AI Tool: ${tool.name}`,
          subtitle: `${tool.domain} • ${tool.description.slice(0, 70)}...`,
          category: "AI Assistant",
          href: `/app/intelligence/activity`,
          badge: tool.status,
        });
      }
    });

    // Shortcut: Launch AI Assistant query
    if (q.length >= 4) {
      results.push({
        id: `ask-ai-${Date.now()}`,
        title: `Ask CampusOS Assistant: "${query}"`,
        subtitle: "Synthesize instant cross-domain analysis with citations",
        category: "AI Assistant",
        href: `/app/intelligence/assistant?q=${encodeURIComponent(query)}`,
        badge: "AI Query",
      });
    }

    return {
      success: true,
      data: results.slice(0, 25),
    };
  }
}

export const searchService = new SearchService();
