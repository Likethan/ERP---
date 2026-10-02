import { ApiResponse } from "@campusos/types";
import { GuardianRecord } from "@/types/people";
import { studentsService } from "./students.service";

/**
 * Dedicated Guardians Service
 * Provides canonical guardian relationship mutations and queries.
 */
class GuardiansService {
  async getGuardians(studentId: string): Promise<ApiResponse<GuardianRecord[]>> {
    return studentsService.getGuardians(studentId);
  }

  async addGuardian(studentId: string, data: Partial<GuardianRecord>): Promise<ApiResponse<GuardianRecord>> {
    return studentsService.addGuardian(studentId, data);
  }

  async updateGuardian(studentId: string, guardianId: string, data: Partial<GuardianRecord>): Promise<ApiResponse<GuardianRecord>> {
    return studentsService.updateGuardian(studentId, guardianId, data);
  }

  async removeGuardian(studentId: string, guardianId: string): Promise<ApiResponse<boolean>> {
    return studentsService.deleteGuardian(studentId, guardianId);
  }
}

export const guardiansService = new GuardiansService();
