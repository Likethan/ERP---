# CampusOS — Campus Infrastructure Operations (Hostel, Transport, Facilities & Maintenance) Frontend Architecture

## 1. Executive Overview

The **Campus Infrastructure Operations** module is the physical foundation and logistics command layer of **CampusOS**.

Following the unified CampusOS institutional sequence:
```text
People → Academics → Attendance → Examinations → Finance → Placement → Campus → Infrastructure
```

The Infrastructure module governs the physical campus lifecycle: residential hostel living, daily bus transport & student boarding passes, campus physical facilities & equipment asset registries, and the campus-wide engineering maintenance & work order dispatch desk.

---

## 2. Core Infrastructure Lifecycle

```text
Hostel / Route / Facility Asset
               ↓
Student / Staff Allocation & Boarding Pass
               ↓
Daily Operational Utilization (Occupancy / Fleet / Room Check-in)
               ↓
Incident / Complaint / Work Order Inception
               ↓
Warden Review / Technician Dispatch / SLA Countdown
               ↓
Resolution Execution & Maintenance Cost Accounting
               ↓
Audit History Logging & Executive Operational Telemetry
```

---

## 3. Absolute Frontend-Only Guarantee

- **Zero Backend Business Logic**: No backend database models, migrations, schemas, repositories, or router endpoints in `apps/api` were modified or created.
- **Service Isolation**: All UI pages consume typed service interfaces via `infrastructureService`, `hostelsService`, `hostelRoomsService`, `hostelLeavesService`, `hostelComplaintsService`, `transportRoutesService`, `transportStopsService`, `transportVehiclesService`, `transportDriversService`, `transportAllocationsService`, `facilitiesService`, `maintenanceService`, and `infrastructureReportsService`.
- **Pure Calculators**: Centralized deterministic calculation functions in `infrastructure-calculator.ts` eliminate formula duplication.
- **Relational Mock Adapter**: Fully synchronized in-memory database linking hostel blocks, rooms, bed status, gate pass leaves, tickets, bus routes, pick-up stops, vehicle fleet, drivers, passes, facilities, equipment, work orders, and analytics.

---

## 4. Route Architecture & Directory Map

| Route | View Description | Primary Persona | Key Capabilities |
| :--- | :--- | :--- | :--- |
| `/app/infrastructure` | Executive Infrastructure Operations Command Center | All Roles | KPI metric banners (Hostel occupancy, transport fleet, facilities attention, open work orders), emergency alerts, quick launchpad |
| `/app/infrastructure/hostel` | Hostel Blocks & Residential Directory | Wardens, Admin, Students | Hostel block cards, gender segregation, occupancy progress bars, block warden contact info, view rooms shortcut |
| `/app/infrastructure/hostel/rooms` | Room & Bed Inventory Matrix | Wardens, Estate Managers | Room grid, floor filters, bed status badges (Available, Occupied, Maintenance), direct bed allocation/vacate modal |
| `/app/infrastructure/hostel/allocations` | Student Hostel Bed Allocations Desk | Wardens, Admin | Enterprise DataGrid of student residents, roll number search, room & bed assignments, checkout/relocation actions |
| `/app/infrastructure/hostel/leaves` | Hostel Leave & Gate Pass Approval Console | Wardens, Security Officers | Student leave requests, emergency parent contact, 1-click Warden Approve/Reject, security gate pass code generator |
| `/app/infrastructure/hostel/complaints` | Residential Grievances & Work Orders | Wardens, Students, Technicians | Ticket queue, category filters (Plumbing, Electrical, Wi-Fi, Furniture), SLA timer, technician dispatch modal |
| `/app/infrastructure/hostel/complaints/[id]` | Grievance Command & Repair Tracker | Wardens, Students, Technicians | Full incident profile, activity audit log, technician assignment, status transition with resolution notes |
| `/app/infrastructure/transport` | Campus Fleet & Transport Logistics Command | Transport Officers, Admin | Fleet status KPIs, route loads, driver schedules, vehicle fitness alerts, route dispatch launchpad |
| `/app/infrastructure/transport/routes` | Bus Route Catalog & Stop Sequences | Transport Officers, Students | Active routes, morning/evening schedules, passenger loads, route capacity utilization bars, stops sequence modal |
| `/app/infrastructure/transport/stops` | Pick-Up & Drop Points Registry | Transport Officers | Geo-landmark stops, sequence orders, passenger boarding counts, route assignments |
| `/app/infrastructure/transport/vehicles` | Vehicle Fleet Registry & Fitness Desk | Transport Officers, Mechanics | Bus/Van fleet list, capacity, fuel type (Diesel, EV, CNG), insurance & fitness certificate expiration dates, create vehicle |
| `/app/infrastructure/transport/drivers` | Transport Drivers & Pilots Registry | Transport Officers | Licensed drivers, commercial badge numbers, contact numbers, assigned route & bus, license validity alerts |
| `/app/infrastructure/transport/allocations` | Student Transport Pass Desk | Transport Officers, Students | Student boarding pass records, route & stop binding, fee clearance status, pass issuance & cancel modal |
| `/app/infrastructure/transport/allocations/[id]` | Student Transport Pass Detail & QR Pass | Students, Conductors | Pass credentials, student details, pickup stop, route timetable, pass cancellation workflow |
| `/app/infrastructure/facilities` | Campus Physical Assets & Facilities Registry | Facility Officers, Admin | Searchable facility directory, building & floor breakdown, capacity, equipment inventory, register facility modal |
| `/app/infrastructure/maintenance` | Unified Work Orders & Estate Engineering Desk | Facility Officers, Technicians | Priority-based work order queue, SLA countdown timers, technician assignment, status transition, cost tracking |
| `/app/infrastructure/reports` | Multi-Tab Infrastructure Analytics & Telemetry | Executives, Administrators | Multi-tab analytics: Hostel occupancy trends, transport route loads, facility uptime, SLA compliance metrics |

---

## 5. Pure Deterministic Domain Calculators

All infrastructure metrics are derived through pure, deterministic functions in `apps/web/src/services/infrastructure-calculator.ts`:

- `calculateHostelOccupancy(occupiedBeds, totalBeds)`: Clamped percentage (0–100%) rounded to 1 decimal place.
- `calculateRoomOccupancy(occupiedBeds, capacityBeds)`: Room-level utilization metric.
- `calculateBedAvailability(totalBeds, occupiedBeds, maintenanceBeds)`: Accurately separates usable beds from maintenance downtime.
- `calculateRouteUtilization(allocatedStudents, capacity)`: Route load tracking for fleet balancing.
- `calculateVehicleUtilization(assignedRoutesCapacity, totalFleetCapacity)`: Fleet deployment efficiency.
- `calculateTransportAllocationRate(allocatedStudents, totalEligibleStudents)`: Campus transit adoption rate.
- `calculateComplaintResolutionRate(resolvedCount, totalComplaints)`: Residential service quality metric.
- `calculateMaintenanceResolutionRate(resolvedRequests, totalRequests)`: Engineering department efficiency.
- `calculateMaintenanceSLAStatus(createdAtIso, priority, resolvedAtIso)`: Real-time SLA compliance tracking against institutional targets (Critical: 4h, High: 12h, Medium: 24h, Low: 48h).
- `calculateFacilityAvailability(totalFacilities, maintenanceFacilities)`: Physical asset uptime metric.
