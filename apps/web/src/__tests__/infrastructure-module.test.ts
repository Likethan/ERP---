/**
 * CampusOS Infrastructure Operations (Hostel, Transport, Facilities & Maintenance) — Comprehensive Test Suite
 * Validates domain contracts, pure arithmetic calculators, hostel allocations & leave passes,
 * transport routes, vehicles, drivers & student passes, facility asset registry,
 * work orders & maintenance SLA workflows, analytics reports, and role-based permissions.
 */

import { infrastructureService } from "../services/infrastructure.service";
import { hostelsService } from "../services/hostels.service";
import { hostelRoomsService } from "../services/hostel-rooms.service";
import { hostelLeavesService } from "../services/hostel-leaves.service";
import { hostelComplaintsService } from "../services/hostel-complaints.service";
import {
  transportRoutesService,
  transportVehiclesService,
  transportDriversService,
} from "../services/transport.service";
import { transportAllocationsService } from "../services/transport-allocations.service";
import { facilitiesService } from "../services/facilities.service";
import { maintenanceService } from "../services/maintenance.service";
import { infrastructureReportsService } from "../services/infrastructure-reports.service";
import {
  calculateHostelOccupancy,
  calculateRoomOccupancy,
  calculateBedAvailability,
  calculateRouteUtilization,
  calculateVehicleUtilization,
  calculateTransportAllocationRate,
  calculateComplaintResolutionRate,
  calculateMaintenanceResolutionRate,
  calculateMaintenanceSLAStatus,
  calculateFacilityAvailability,
} from "../services/infrastructure-calculator";
import {
  BedStatus,
  LeaveStatus,
  ComplaintStatus,
  ComplaintPriority,
  MaintenanceStatus,
  MaintenancePriority,
  FacilityType,
  FacilityStatus,
  VehicleStatus,
  VehicleType,
  TransportAllocationStatus,
} from "@campusos/types";
import { DEMO_PERSONAS } from "../mocks/auth.mock";

export async function runInfrastructureModuleTests(): Promise<{
  passed: number;
  failed: number;
  results: { testName: string; passed: boolean; message?: string }[];
}> {
  const results: { testName: string; passed: boolean; message?: string }[] = [];

  function assert(condition: unknown, testName: string, failureDetails?: string) {
    if (Boolean(condition)) {
      results.push({ testName, passed: true });
    } else {
      results.push({ testName, passed: false, message: failureDetails || "Assertion failed" });
    }
  }

  try {
    // ==========================================
    // 1. Executive Dashboard & Telemetry
    // ==========================================
    const dashRes = await infrastructureService.getInfrastructureDashboard();
    assert(dashRes.success === true, "1. Infrastructure dashboard telemetry returns success");
    assert(dashRes.data.totalHostels >= 3, "1. Total hostels tracked correctly");
    assert(dashRes.data.hostelOccupancyPercentage > 0, "1. Overall hostel occupancy rate calculated");
    assert(dashRes.data.activeTransportRoutes >= 4, "1. Transport routes count tracked");
    assert(dashRes.data.studentsUsingTransport > 0, "1. Active student transport passes tracked");
    assert(dashRes.data.openMaintenanceRequests >= 0, "1. Open maintenance requests tracked");
    assert(dashRes.data.availableBeds >= 0, "1. Available beds tracked");

    // ==========================================
    // 2. Centralized Pure Calculators
    // ==========================================
    // Hostel Occupancy
    const occ1 = calculateHostelOccupancy(420, 500);
    assert(occ1 === 84, `2. calculateHostelOccupancy(420, 500) = 84% (got ${occ1})`);
    const occClamped = calculateHostelOccupancy(600, 500);
    assert(occClamped === 100, `2. calculateHostelOccupancy clamps overflow to 100% (got ${occClamped})`);
    const occZero = calculateHostelOccupancy(0, 500);
    assert(occZero === 0, "2. calculateHostelOccupancy handles zero occupied beds");
    const occEmpty = calculateHostelOccupancy(100, 0);
    assert(occEmpty === 0, "2. calculateHostelOccupancy handles zero total beds safely");

    // Room Occupancy
    const roomOcc = calculateRoomOccupancy(3, 4);
    assert(roomOcc === 75, `2. calculateRoomOccupancy(3, 4) = 75% (got ${roomOcc})`);

    // Bed Availability
    const bedAvail = calculateBedAvailability(100, 80, 5);
    assert(bedAvail.usableBeds === 95, "2. calculateBedAvailability computes usable beds");
    assert(bedAvail.availableBeds === 15, "2. calculateBedAvailability computes remaining available beds");
    assert(bedAvail.availabilityRate === 15, "2. calculateBedAvailability computes availability rate");

    // Transport Utilization
    const routeUtil = calculateRouteUtilization(48, 52);
    assert(routeUtil === 92.3, `2. calculateRouteUtilization(48, 52) = 92.3% (got ${routeUtil})`);
    const vehUtil = calculateVehicleUtilization(400, 500);
    assert(vehUtil === 80, `2. calculateVehicleUtilization(400, 500) = 80% (got ${vehUtil})`);
    const allocRate = calculateTransportAllocationRate(350, 1000);
    assert(allocRate === 35, `2. calculateTransportAllocationRate(350, 1000) = 35% (got ${allocRate})`);

    // Resolution Rates
    const compRate = calculateComplaintResolutionRate(18, 20);
    assert(compRate === 90, `2. calculateComplaintResolutionRate(18, 20) = 90% (got ${compRate})`);
    const maintRate = calculateMaintenanceResolutionRate(45, 50);
    assert(maintRate === 90, `2. calculateMaintenanceResolutionRate(45, 50) = 90% (got ${maintRate})`);

    // Facility Availability
    const facAvail = calculateFacilityAvailability(20, 2);
    assert(facAvail === 90, `2. calculateFacilityAvailability(20, 2) = 90% (got ${facAvail})`);

    // Maintenance SLA Calculations
    const slaCritical = calculateMaintenanceSLAStatus(new Date(Date.now() - 2 * 3600 * 1000).toISOString(), MaintenancePriority.CRITICAL);
    assert(slaCritical.slaTargetHours === 4, "2. CRITICAL maintenance target is 4 hours");
    assert(slaCritical.isBreached === false, "2. 2-hour elapsed critical request is not breached");

    const slaBreached = calculateMaintenanceSLAStatus(new Date(Date.now() - 6 * 3600 * 1000).toISOString(), MaintenancePriority.CRITICAL);
    assert(slaBreached.isBreached === true, "2. 6-hour elapsed critical request is marked breached");
    assert(slaBreached.statusText === "BREACHED", "2. Status text is BREACHED");

    const slaResolvedOnTime = calculateMaintenanceSLAStatus(
      "2026-09-01T10:00:00Z",
      MaintenancePriority.MEDIUM,
      "2026-09-01T18:00:00Z"
    );
    assert(slaResolvedOnTime.statusText === "RESOLVED_WITHIN_SLA", "2. SLA resolved within window detected");

    // ==========================================
    // 3. Hostel Operations & Room Inventory
    // ==========================================
    const hostelsRes = await hostelsService.listHostels();
    assert(hostelsRes.success === true && hostelsRes.data.length >= 3, "3. List hostels returns registered blocks");
    const testHostel = hostelsRes.data[0];

    const hostelDetail = await hostelsService.getHostelById(testHostel.id);
    assert(hostelDetail.success === true && hostelDetail.data?.id === testHostel.id, "3. Get hostel by ID returns full profile");

    const roomsRes = await hostelRoomsService.listRooms({ hostelId: testHostel.id });
    assert(roomsRes.success === true && roomsRes.data.length > 0, "3. List rooms retrieves rooms for hostel");
    const testRoom = roomsRes.data[0];

    // Bed Allocation Lifecycle
    const availableBed = testRoom.beds.find((b) => b.status === BedStatus.AVAILABLE);
    if (availableBed) {
      const allocBedRes = await hostelRoomsService.allocateBed(
        testRoom.id,
        availableBed.id,
        "stu-test-infra-01",
        "Kiran Kumar",
        "22CS101"
      );
      assert(allocBedRes.success === true, "3. Bed allocation successful");
      assert(allocBedRes.data?.beds.find((b) => b.id === availableBed.id)?.status === BedStatus.OCCUPIED, "3. Allocated bed status set to OCCUPIED");

      // Deallocate
      const deallocRes = await hostelRoomsService.deallocateBed(testRoom.id, availableBed.id);
      assert(deallocRes.success === true, "3. Bed deallocation successful");
      assert(deallocRes.data?.beds.find((b) => b.id === availableBed.id)?.status === BedStatus.AVAILABLE, "3. Bed status restored to AVAILABLE");
    }

    // ==========================================
    // 4. Hostel Leaves & Outing Passes
    // ==========================================
    const leavesRes = await hostelLeavesService.listLeaves();
    assert(leavesRes.success === true && leavesRes.data.length > 0, "4. List hostel leaves returns requests");

    const newLeaveRes = await hostelLeavesService.createLeaveRequest({
      studentId: "stu-leave-test",
      studentName: "Ananya Sharma",
      registerNumber: "23EC044",
      hostelId: testHostel.id,
      hostelName: testHostel.name,
      roomNumber: testRoom.roomNumber,
      leaveType: "WEEKEND",
      startDate: "2026-10-10",
      endDate: "2026-10-12",
      reason: "Family gathering at hometown",
      parentContactNumber: "+91 98450 12345",
    });
    assert(newLeaveRes.success === true, "4. Submit hostel leave request succeeds");
    assert(newLeaveRes.data.approvalStatus === LeaveStatus.PENDING, "4. Initial leave status is PENDING");

    // Approve leave
    const approveRes = await hostelLeavesService.approveLeave(newLeaveRes.data.id, "Dr. S. Ramanathan (Warden)");
    assert(approveRes.success === true && approveRes.data?.approvalStatus === LeaveStatus.APPROVED, "4. Warden leave approval succeeds");
    assert(approveRes.data?.approvedBy !== null, "4. Approved leave records approver");

    // ==========================================
    // 5. Hostel Complaints & Maintenance Escalation
    // ==========================================
    const compRes = await hostelComplaintsService.listComplaints();
    assert(compRes.success === true && compRes.data.length > 0, "5. List hostel complaints returns issues");

    const newComp = await hostelComplaintsService.createComplaint({
      studentId: "stu-comp-01",
      studentName: "Rohit Verma",
      hostelId: testHostel.id,
      hostelName: testHostel.name,
      roomNumber: testRoom.roomNumber,
      category: "PLUMBING",
      priority: ComplaintPriority.HIGH,
      title: "Bathroom tap leaking continuously",
      description: "Severe drip causing water pooling on floor since morning.",
    });
    assert(newComp.success === true, "5. Create hostel complaint succeeds");
    assert(newComp.data.status === ComplaintStatus.OPEN, "5. Initial complaint status is OPEN");

    // Assign technician
    const assignComp = await hostelComplaintsService.assignComplaint(newComp.data.id, "Ramesh Kumar (Plumber)", "Warden Desk");
    assert(assignComp.success === true && assignComp.data?.status === ComplaintStatus.ASSIGNED, "5. Assigning technician sets status to ASSIGNED");

    // Resolve complaint
    const resolveComp = await hostelComplaintsService.updateComplaintStatus(
      newComp.data.id,
      ComplaintStatus.RESOLVED,
      "Ramesh Kumar",
      "Replaced faulty brass valve cartridge and tested under full pressure."
    );
    assert(resolveComp.success === true && resolveComp.data?.status === ComplaintStatus.RESOLVED, "5. Complaint successfully resolved");

    // ==========================================
    // 6. Transport Routes, Vehicles & Drivers
    // ==========================================
    const routesRes = await transportRoutesService.listRoutes();
    assert(routesRes.success === true && routesRes.data.length >= 4, "6. Transport routes list returns active routes");
    const testRoute = routesRes.data[0];

    const stopsRes = await transportRoutesService.getStopsByRouteId(testRoute.id);
    assert(stopsRes.success === true && stopsRes.data.length > 0, "6. Route stops list returns scheduled pick-up points");

    const vehiclesRes = await transportVehiclesService.listVehicles();
    assert(vehiclesRes.success === true && vehiclesRes.data.length > 0, "6. Transport vehicle fleet catalog retrieved");

    // Create new vehicle
    const newVehRes = await transportVehiclesService.createVehicle({
      registrationNumber: "KA-04-E-9999",
      vehicleNumber: "BUS-24",
      type: VehicleType.BUS,
      makeModel: "Ashok Leyland Viking 54-Seater",
      capacity: 54,
      fuelType: "DIESEL",
      insuranceValidUntil: "2027-12-31",
      fitnessCertificateValidUntil: "2027-10-31",
      status: VehicleStatus.AVAILABLE,
    });
    assert(newVehRes.success === true, "6. Register new fleet vehicle succeeds");

    const driversRes = await transportDriversService.listDrivers();
    assert(driversRes.success === true && driversRes.data.length > 0, "6. Transport drivers list returns registered pilots");

    // ==========================================
    // 7. Student Transport Pass Allocations
    // ==========================================
    const allocsRes = await transportAllocationsService.listTransportAllocations();
    assert(allocsRes.success === true && allocsRes.data.length > 0, "7. Transport pass allocations catalog retrieved");

    const newPassRes = await transportAllocationsService.createTransportAllocation({
      studentId: "stu-pass-01",
      studentName: "Deepak Menon",
      registerNumber: "22ME077",
      routeId: testRoute.id,
      routeName: testRoute.name,
      routeCode: testRoute.routeCode,
      stopId: stopsRes.data[0].id,
      stopName: stopsRes.data[0].name,
      vehicleId: newVehRes.data.id,
      vehicleNumber: newVehRes.data.vehicleNumber,
      seatNumber: "S-14",
      feeStatus: "PAID",
    });
    assert(newPassRes.success === true, "7. Create student transport pass succeeds");
    assert(newPassRes.data.status === TransportAllocationStatus.ACTIVE, "7. New transport pass is ACTIVE");

    // Cancel pass
    const cancelPassRes = await transportAllocationsService.cancelTransportAllocation(newPassRes.data.id, "Student moved to campus hostel");
    assert(cancelPassRes.success === true && cancelPassRes.data?.status === TransportAllocationStatus.CANCELLED, "7. Cancel transport pass succeeds");

    // ==========================================
    // 8. Facilities & Campus Asset Catalog
    // ==========================================
    const facList = await facilitiesService.listFacilities();
    assert(facList.success === true && facList.data.length >= 5, "8. Facilities catalog returns campus assets");

    const newFac = await facilitiesService.createFacility({
      name: "Robotics & Embedded Systems Center",
      code: "FAC-ROB-01",
      campusId: "campus-main",
      campusName: "Main Campus",
      building: "Technology Tower",
      floor: 4,
      type: FacilityType.LABORATORY,
      capacity: 60,
      status: FacilityStatus.ACTIVE,
      managerName: "Prof. Arvind Swaminathan",
      managerEmail: "arvind.s@campus.edu",
      managerPhone: "+91 94480 11223",
      departmentCode: "ECE",
    });
    assert(newFac.success === true, "8. Register new facility succeeds");
    assert(newFac.data.type === FacilityType.LABORATORY, "8. Registered facility type preserved");

    // ==========================================
    // 9. Work Orders & Campus Maintenance Desk
    // ==========================================
    const maintList = await maintenanceService.listMaintenanceRequests();
    assert(maintList.success === true && maintList.data.length > 0, "9. List maintenance work orders succeeds");

    const newWO = await maintenanceService.createMaintenanceRequest({
      assetOrFacilityId: newFac.data.id,
      assetOrFacilityName: newFac.data.name,
      category: "ELECTRICAL",
      sourceType: "FACILITY",
      location: "Technology Tower, Floor 4, Lab 402",
      reportedBy: {
        userId: "usr-admin",
        name: "Campus Facility Officer",
        role: "FACILITY_OFFICER",
      },
      priority: MaintenancePriority.HIGH,
      title: "Three-phase distribution board tripping under load",
      description: "Circuit breaker trips whenever multiple robotic arms are powered simultaneously.",
      estimatedCostInr: 12000,
    });
    assert(newWO.success === true, "9. Issue maintenance work order succeeds");
    assert(newWO.data.status === MaintenanceStatus.REQUESTED, "9. Initial work order status is REQUESTED");
    assert(newWO.data.slaTargetHours === 12, "9. HIGH priority work order assigned 12-hour SLA");

    // Assign technician
    const assignWO = await maintenanceService.assignMaintenanceTechnician(newWO.data.id, {
      staffId: "stf-elec-04",
      name: "Ganesh Moorthy",
      department: "Estate Electrical Division",
      phone: "+91 98450 44556",
    });
    assert(assignWO.success === true && assignWO.data?.status === MaintenanceStatus.ASSIGNED, "9. Assigning technician sets status to ASSIGNED");

    // Transition status to RESOLVED
    const resolveWO = await maintenanceService.updateMaintenanceStatus(newWO.data.id, {
      status: MaintenanceStatus.RESOLVED,
      changedBy: "Ganesh Moorthy (Senior Electrician)",
      resolutionSummary: "Replaced 32A MCB with 63A D-curve breaker and re-balanced phase loads across lab benches.",
      actualCostInr: 9500,
    });
    assert(resolveWO.success === true && resolveWO.data?.status === MaintenanceStatus.RESOLVED, "9. Work order successfully resolved");
    assert(resolveWO.data?.actualCostInr === 9500, "9. Work order actual cost recorded");
    assert((resolveWO.data?.history?.length ?? 0) >= 3, "9. Work order audit history preserved");

    // ==========================================
    // 10. Multi-Tab Analytics Reports
    // ==========================================
    const reportsSummary = await infrastructureReportsService.getInfrastructureReports();
    assert(reportsSummary.success === true, "10. Analytics reports summary succeeds");
    assert(reportsSummary.data.hostelSummary.hostelWiseStats.length >= 3, "10. Hostel occupancy report records all hostel blocks");
    assert(reportsSummary.data.transportSummary.routeUtilization.length >= 4, "10. Transport route load metrics computed");
    assert(reportsSummary.data.maintenanceSummary.priorityDistribution.length >= 4, "10. Maintenance SLA compliance report covers priorities");
    assert(reportsSummary.data.facilitiesSummary.totalFacilities >= 5, "10. Facilities summary metrics computed");

    // ==========================================
    // 11. Role-Based Access Control (RBAC)
    // ==========================================
    const superAdmin = DEMO_PERSONAS.find((p) => p.role === "SUPER_ADMIN");
    const warden = DEMO_PERSONAS.find((p) => p.role === "WARDEN");
    const transportOfficer = DEMO_PERSONAS.find((p) => p.role === "TRANSPORT_OFFICER");
    const facilityOfficer = DEMO_PERSONAS.find((p) => p.role === "FACILITY_OFFICER");
    const student = DEMO_PERSONAS.find((p) => p.role === "STUDENT");

    assert(superAdmin?.permissions.includes("*"), "11. Super Admin holds wildcard permissions");
    assert(
      warden?.permissions.includes("hostel.approve_leaves") ||
      warden?.permissions.includes("hostel.manage_rooms") ||
      warden?.role === "WARDEN",
      "11. Warden authorized for hostel administration"
    );
    assert(
      transportOfficer?.permissions.includes("transport.manage_routes") ||
      transportOfficer?.role === "TRANSPORT_OFFICER",
      "11. Transport Officer authorized for fleet and routes"
    );
    assert(
      facilityOfficer?.permissions.includes("facilities.manage") ||
      facilityOfficer?.role === "FACILITY_OFFICER",
      "11. Facility Officer authorized for campus facilities and work orders"
    );
    assert(student?.role === "STUDENT", "11. Student persona verified for leaf-level requests");

  } catch (err: any) {
    results.push({ testName: "Global Execution Catch", passed: false, message: err.message });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;

  return { passed, failed, results };
}

if (typeof process !== "undefined" && process.argv[1]?.includes("infrastructure-module.test")) {
  runInfrastructureModuleTests().then((res) => {
    console.log(`\n======================================================`);
    console.log(`CampusOS Infrastructure Operations Module Test Results:`);
    console.log(`Passed: ${res.passed}, Failed: ${res.failed}`);
    console.log(`======================================================`);
    res.results.forEach((r) => {
      console.log(`${r.passed ? "✔ PASS" : "✖ FAIL"}: ${r.testName}${r.message ? ` (${r.message})` : ""}`);
    });
    if (res.failed > 0) {
      process.exit(1);
    }
  });
}
