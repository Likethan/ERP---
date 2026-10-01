import { ApiResponse } from "@campusos/types";
import {
  CompanyProfileItem,
  JobDriveItem,
  PlacementOfferItem,
  MOCK_COMPANIES,
  MOCK_JOB_DRIVES,
  MOCK_OFFERS,
} from "@/mocks/placements.mock";

class PlacementsService {
  private companies: CompanyProfileItem[] = [...MOCK_COMPANIES];
  private drives: JobDriveItem[] = [...MOCK_JOB_DRIVES];
  private offers: PlacementOfferItem[] = [...MOCK_OFFERS];

  async getCompanies(): Promise<ApiResponse<CompanyProfileItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.companies };
  }

  async getDrives(status?: string): Promise<ApiResponse<JobDriveItem[]>> {
    await new Promise((r) => setTimeout(r, 50));
    let items = [...this.drives];
    if (status) {
      items = items.filter((d) => d.status === status);
    }
    return { success: true, data: items };
  }

  async getDriveById(id: string): Promise<ApiResponse<JobDriveItem | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const drive = this.drives.find((d) => d.id === id) || null;
    return { success: true, data: drive };
  }

  async getOffers(): Promise<ApiResponse<PlacementOfferItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.offers };
  }

  async createDrive(data: Partial<JobDriveItem>): Promise<ApiResponse<JobDriveItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const newDrive: JobDriveItem = {
      id: `drive-${Date.now()}`,
      companyName: data.companyName || "Recruiter",
      roleTitle: data.roleTitle || "Associate Engineer",
      packageLPA: data.packageLPA || 10.0,
      driveDate: data.driveDate || new Date().toISOString().split("T")[0],
      applicationDeadline: data.applicationDeadline || new Date().toISOString().split("T")[0],
      targetPrograms: data.targetPrograms || ["B.Tech CSE"],
      minimumCGPA: data.minimumCGPA || 7.5,
      maxBacklogsAllowed: data.maxBacklogsAllowed || 0,
      minAttendancePercent: data.minAttendancePercent || 75,
      location: data.location || "Bengaluru Campus",
      totalApplicants: 0,
      shortlistedCount: 0,
      offersMadeCount: 0,
      status: "APPLICATIONS_OPEN",
    };
    this.drives.unshift(newDrive);
    return { success: true, data: newDrive };
  }

  async getAnalytics(): Promise<ApiResponse<{
    total_eligible_students: number;
    placed_students_count: number;
    placement_percentage: number;
    average_ctc_lpa: number;
    highest_ctc_lpa: number;
    total_companies_visited: number;
    active_drives_count: number;
    total_offers_extended: number;
  }>> {
    await new Promise((r) => setTimeout(r, 40));
    return {
      success: true,
      data: {
        total_eligible_students: 420,
        placed_students_count: 386,
        placement_percentage: 91.9,
        average_ctc_lpa: 14.8,
        highest_ctc_lpa: 48.0,
        total_companies_visited: this.companies.length || 48,
        active_drives_count: this.drives.filter((d) => d.status === "APPLICATIONS_OPEN").length || 6,
        total_offers_extended: 462,
      },
    };
  }

  async createCompany(data: Partial<CompanyProfileItem>): Promise<ApiResponse<CompanyProfileItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const newComp: CompanyProfileItem = {
      id: `comp-${Date.now()}`,
      name: data.name || "Enterprise Partner",
      industry: data.industry || "Software & Technology",
      tier: (data.tier as any) || "TIER_1_SUPER_DREAM",
      headquarters: data.headquarters || "Bangalore, India",
      website: data.website || "https://partner.enterprise.com",
      hrContact: data.hrContact || {
        name: "Corporate HR Lead",
        email: "campus-hiring@enterprise.com",
        phone: "+91 80 2841 0000",
      },
      activeDrivesCount: 1,
      totalHiredAlumni: 0,
      status: "ACTIVE",
    };
    this.companies.unshift(newComp);
    return { success: true, data: newComp };
  }

  async applyToDrive(driveId: string): Promise<ApiResponse<{ applicationNumber: string }>> {
    await new Promise((r) => setTimeout(r, 90));
    const drive = this.drives.find((d) => d.id === driveId);
    if (drive) {
      drive.totalApplicants += 1;
    }
    return {
      success: true,
      data: {
        applicationNumber: `APP-${Date.now().toString().slice(-6)}`,
      },
    };
  }

  async submitOfferDecision(offerId: string, decision: "ACCEPT" | "DECLINE"): Promise<ApiResponse<PlacementOfferItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const offer = this.offers.find((o) => o.id === offerId);
    if (offer) {
      offer.acceptanceStatus = decision === "ACCEPT" ? "ACCEPTED" : "DECLINED";
    }
    return { success: true, data: offer || this.offers[0] };
  }
}

export const placementsService = new PlacementsService();
