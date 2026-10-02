# CampusOS — Campus Infrastructure Operations API Contracts & Service Specifications

## 1. Executive Protocol & Envelope Architecture

All infrastructure frontend service calls adhere to the unified standard envelope format:

```typescript
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string | {
    code: string;
    message: string;
    details?: any;
  } | null;
  message?: string;
}
```

---

## 2. Infrastructure Dashboard Telemetry

### `GET /api/v1/infrastructure/dashboard`
Returns high-level institutional infrastructure telemetry.

```typescript
interface InfrastructureDashboardSummary {
  totalHostels: number;
  totalBeds: number;
  occupiedBeds: number;
  availableBeds: number;
  hostelOccupancyPercentage: number;
  activeTransportRoutes: number;
  activeVehicles: number;
  studentsUsingTransport: number;
  openComplaints: number;
  openMaintenanceRequests: number;
  criticalMaintenance: number;
  facilitiesRequiringAttention: number;
}
```

---

## 3. Hostel Operations & Residential Directory

### `GET /api/v1/infrastructure/hostels`
Query params: `{ campusId?: string; type?: HostelType; search?: string }`
Response: `ApiResponse<Hostel[]>`

### `GET /api/v1/infrastructure/hostels/:id`
Response: `ApiResponse<Hostel | null>`

### `GET /api/v1/infrastructure/hostels/:id/rooms`
Query params: `{ floor?: number; status?: RoomStatus; type?: RoomType }`
Response: `ApiResponse<HostelRoom[]>`

### `POST /api/v1/infrastructure/hostel/rooms/:roomId/allocate-bed`
```typescript
interface AllocateBedPayload {
  bedId: string;
  studentId: string;
  studentName: string;
  studentRollNumber: string;
}
```
Response: `ApiResponse<HostelRoom>`

### `POST /api/v1/infrastructure/hostel/rooms/:roomId/deallocate-bed`
```typescript
interface DeallocateBedPayload {
  bedId: string;
}
```
Response: `ApiResponse<HostelRoom>`

---

## 4. Hostel Leaves & Outing Passes

### `GET /api/v1/infrastructure/hostel/leaves`
Query params: `{ hostelId?: string; studentId?: string; approvalStatus?: LeaveStatus; search?: string }`
Response: `ApiResponse<HostelLeave[]>`

### `POST /api/v1/infrastructure/hostel/leaves`
```typescript
interface CreateLeavePayload {
  studentId: string;
  studentName: string;
  registerNumber: string;
  hostelId: string;
  hostelName: string;
  roomNumber: string;
  startDate: string;
  endDate: string;
  reason: string;
  destination: string;
  emergencyContact: {
    name: string;
    relationship: string;
    phone: string;
  };
}
```
Response: `ApiResponse<HostelLeave>`

### `POST /api/v1/infrastructure/hostel/leaves/:id/approve`
```typescript
interface ApproveLeavePayload {
  approvedBy: string;
  remarks?: string;
}
```
Response: `ApiResponse<HostelLeave>`

---

## 5. Hostel Complaints & Residential Grievances

### `GET /api/v1/infrastructure/hostel/complaints`
Query params: `{ hostelId?: string; category?: ComplaintCategory; status?: ComplaintStatus; priority?: ComplaintPriority }`
Response: `ApiResponse<HostelComplaint[]>`

### `POST /api/v1/infrastructure/hostel/complaints`
```typescript
interface CreateComplaintPayload {
  studentId: string;
  studentName: string;
  registerNumber: string;
  hostelId: string;
  hostelName: string;
  roomNumber: string;
  category: ComplaintCategory;
  priority: ComplaintPriority;
  title: string;
  description: string;
}
```
Response: `ApiResponse<HostelComplaint>`

### `PUT /api/v1/infrastructure/hostel/complaints/:id/status`
```typescript
interface UpdateComplaintStatusPayload {
  newStatus: ComplaintStatus;
  actorName: string;
  notes?: string;
}
```
Response: `ApiResponse<HostelComplaint>`

---

## 6. Transport Routes, Stops, Fleet & Passes

### `GET /api/v1/transport/routes`
Response: `ApiResponse<TransportRoute[]>`

### `GET /api/v1/transport/stops`
Query params: `{ routeId?: string; status?: StopStatus }`
Response: `ApiResponse<TransportStop[]>`

### `GET /api/v1/transport/vehicles`
Query params: `{ type?: VehicleType; status?: VehicleStatus }`
Response: `ApiResponse<TransportVehicle[]>`

### `POST /api/v1/transport/vehicles`
```typescript
interface CreateVehiclePayload {
  registrationNumber: string;
  vehicleNumber: string;
  type: VehicleType;
  makeModel: string;
  capacity: number;
  fuelType: "DIESEL" | "EV" | "CNG" | "PETROL";
  insuranceValidUntil: string;
  fitnessCertificateValidUntil: string;
  status: VehicleStatus;
}
```
Response: `ApiResponse<TransportVehicle>`

### `POST /api/v1/transport/allocations`
```typescript
interface CreateTransportAllocationPayload {
  studentId: string;
  studentName: string;
  registerNumber: string;
  routeId: string;
  routeName?: string;
  routeCode?: string;
  stopId: string;
  stopName?: string;
  vehicleId?: string;
  vehicleNumber?: string;
  seatNumber?: string | null;
  feeStatus?: string | null;
}
```
Response: `ApiResponse<TransportAllocation>`

### `POST /api/v1/transport/allocations/:id/cancel`
```typescript
interface CancelAllocationPayload {
  reason?: string;
}
```
Response: `ApiResponse<TransportAllocation>`

---

## 7. Facilities & Work Orders Maintenance Desk

### `GET /api/v1/facilities`
Query params: `{ campusId?: string; type?: FacilityType; status?: FacilityStatus; search?: string }`
Response: `ApiResponse<Facility[]>`

### `POST /api/v1/facilities`
```typescript
interface CreateFacilityPayload {
  name: string;
  code: string;
  campusId: string;
  campusName: string;
  building: string;
  floor: number | string;
  type: FacilityType;
  capacity: number;
  status: FacilityStatus;
  managerName: string;
  managerEmail: string;
  managerPhone: string;
  departmentCode?: string;
}
```
Response: `ApiResponse<Facility>`

### `GET /api/v1/maintenance`
Query params: `{ sourceType?: string; category?: string; priority?: MaintenancePriority; status?: MaintenanceStatus; search?: string }`
Response: `ApiResponse<MaintenanceRequest[]>`

### `POST /api/v1/maintenance`
```typescript
interface CreateMaintenanceRequestPayload {
  assetOrFacilityId: string;
  assetOrFacilityName: string;
  category: "ELECTRICAL" | "PLUMBING" | "CIVIL" | "HVAC" | "IT_EQUIPMENT" | "CARPENTRY" | "TRANSPORT_VEHICLE" | "OTHER";
  sourceType: "HOSTEL" | "ROOM" | "FACILITY" | "VEHICLE" | "EQUIPMENT" | "CAMPUS";
  location: string;
  reportedBy: {
    userId: string;
    name: string;
    role: string;
    phone?: string;
  };
  priority: MaintenancePriority;
  title: string;
  description: string;
  estimatedCostInr?: number;
}
```
Response: `ApiResponse<MaintenanceRequest>`

### `PUT /api/v1/maintenance/:id/status`
```typescript
interface UpdateMaintenanceStatusPayload {
  status: MaintenanceStatus;
  changedBy: string;
  notes?: string;
  resolutionSummary?: string;
  actualCostInr?: number;
}
```
Response: `ApiResponse<MaintenanceRequest>`
