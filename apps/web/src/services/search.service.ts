import { ApiResponse } from "@campusos/types";
import { GlobalSearchResultItem } from "@/types/domain";
import { MOCK_STUDENTS } from "@/mocks/students.mock";
import { MOCK_FACULTY } from "@/mocks/faculty.mock";
import { MOCK_SUBJECTS } from "@/mocks/academics.mock";
import { MOCK_JOB_DRIVES } from "@/mocks/placements.mock";
import { MOCK_INVOICES } from "@/mocks/finance.mock";
import { MOCK_EVENTS } from "@/mocks/campus.mock";
import { MOCK_DOCUMENTS } from "@/mocks/documents.mock";

class SearchService {
  async search(query: string): Promise<ApiResponse<GlobalSearchResultItem[]>> {
    if (!query || query.trim().length < 2) {
      return { success: true, data: [] };
    }

    await new Promise((r) => setTimeout(r, 60));
    const q = query.toLowerCase().trim();
    const results: GlobalSearchResultItem[] = [];

    // Search Students
    MOCK_STUDENTS.forEach((s) => {
      if (
        s.firstName.toLowerCase().includes(q) ||
        s.lastName.toLowerCase().includes(q) ||
        s.rollNumber.toLowerCase().includes(q)
      ) {
        results.push({
          id: s.id,
          title: `${s.firstName} ${s.lastName}`,
          subtitle: `${s.rollNumber} • ${s.program.code} (Sem ${s.currentSemester})`,
          category: "Student",
          href: `/app/students/${s.rollNumber}`,
          badge: s.status,
        });
      }
    });

    // Search Faculty
    MOCK_FACULTY.forEach((f) => {
      if (
        f.firstName.toLowerCase().includes(q) ||
        f.lastName.toLowerCase().includes(q) ||
        f.department.toLowerCase().includes(q)
      ) {
        results.push({
          id: f.id,
          title: `${f.firstName} ${f.lastName}`,
          subtitle: `${f.designation} • ${f.department}`,
          category: "Faculty",
          href: `/app/faculty`,
        });
      }
    });

    // Search Courses
    MOCK_SUBJECTS.forEach((sub) => {
      if (sub.name.toLowerCase().includes(q) || sub.code.toLowerCase().includes(q)) {
        results.push({
          id: sub.id,
          title: `${sub.code} — ${sub.name}`,
          subtitle: `${sub.department} • ${sub.credits} Credits`,
          category: "Course",
          href: `/app/academics/subjects`,
        });
      }
    });

    // Search Placement Drives
    MOCK_JOB_DRIVES.forEach((d) => {
      if (d.companyName.toLowerCase().includes(q) || d.roleTitle.toLowerCase().includes(q)) {
        results.push({
          id: d.id,
          title: `${d.companyName}: ${d.roleTitle}`,
          subtitle: `₹${d.packageLPA} LPA • ${d.location}`,
          category: "Drive",
          href: `/app/placement`,
          badge: d.status,
        });
      }
    });

    // Search Invoices
    MOCK_INVOICES.forEach((inv) => {
      if (
        inv.invoiceNumber.toLowerCase().includes(q) ||
        inv.studentName.toLowerCase().includes(q) ||
        inv.rollNumber.toLowerCase().includes(q)
      ) {
        results.push({
          id: inv.id,
          title: `${inv.invoiceNumber} — ${inv.studentName}`,
          subtitle: `₹${inv.totalAmount.toLocaleString()} • Due: ${inv.dueDate}`,
          category: "Invoice",
          href: `/app/finance/invoices`,
          badge: inv.status,
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
