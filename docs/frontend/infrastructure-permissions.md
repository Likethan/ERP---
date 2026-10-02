# CampusOS — Campus Infrastructure Operations Role-Based Access Control (RBAC) Matrix

## 1. Persona Taxonomy

The Infrastructure Operations module supports 5 key user personas with granular operational authorities:

1. **Super Admin / Estate Director**: Complete governance over hostels, fleet, assets, budgets, and staff.
2. **Hostel Warden / Residential Officer**: Hostel blocks, room allocations, leave gate passes, and residential grievances.
3. **Transport Officer / Logistics Lead**: Bus routes, pick-up stops, fleet vehicles, certified drivers, and student boarding passes.
4. **Facility Officer / Estate Engineer**: Campus facilities, laboratory assets, work orders desk, technician dispatch, and SLA compliance.
5. **Student Resident / Commuter**: Bed status inquiry, leave gate pass requests, bus pass booking, and maintenance grievance logging.

---

## 2. Granular Permissions Matrix

| Functional Capability | Super Admin | Hostel Warden | Transport Officer | Facility Officer | Student |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Executive Dashboard & Telemetry** | Full | Read | Read | Read | Restricted |
| **View Hostel Blocks & Rooms** | Full | Full | Read | Read | Read (Own Block) |
| **Allocate / Vacate Hostel Beds** | Full | Full | Denied | Denied | Denied |
| **Approve / Reject Hostel Leaves** | Full | Full | Denied | Denied | Denied |
| **Request Hostel Leave & Gate Pass** | Full | Denied | Denied | Denied | Full (Own Request) |
| **Log Hostel Complaint / Grievance** | Full | Full | Denied | Read | Full (Own Room) |
| **Assign Complaint Technician** | Full | Full | Denied | Full | Denied |
| **Manage Bus Routes & Stops** | Full | Denied | Full | Denied | Read |
| **Manage Fleet Vehicles & Inspection** | Full | Denied | Full | Denied | Denied |
| **Manage Transport Drivers** | Full | Denied | Full | Denied | Denied |
| **Issue / Cancel Student Bus Passes** | Full | Denied | Full | Denied | Self (Book / Cancel) |
| **Register / Edit Facilities** | Full | Denied | Denied | Full | Read |
| **Issue Maintenance Work Order** | Full | Full | Full | Full | Denied (Staff Only) |
| **Dispatch Technician & Update SLA** | Full | Read | Read | Full | Denied |
| **Close Work Order & Record Costs** | Full | Read | Read | Full | Denied |
| **Executive Multi-Tab Reports** | Full | Hostel Tabs | Transport Tabs | Facilities Tabs | Denied |

---

## 3. Security Boundary Rules

1. **Student Boundary Rule**: Students can never access administrative allocation desks, approve gate passes, edit route configurations, or resolve maintenance work orders.
2. **Estate Boundary Rule**: Transport Officers cannot modify residential hostel beds, and Hostel Wardens cannot reassign bus routes.
3. **Audit Immutability**: All status transitions (Work orders, leave gate passes, bed allocations) maintain an append-only audit trail logging timestamp, actor identity, and operational remarks.
