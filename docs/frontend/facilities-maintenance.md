# CampusOS — Campus Facilities Registry & Work Orders Maintenance Desk

## 1. Executive Overview

The Facilities & Maintenance module unifies physical campus asset governance with estate engineering operations. It ensures institutional buildings, laboratories, auditoriums, and utility networks operate at peak efficiency.

```text
Facility Asset Charter (Buildings, Labs, Equipment)
                     ↓
Incident Inception (Hostel / Campus / Transport)
                     ↓
Work Order Generated & Priority Assigned
                     ↓
Technician Dispatch & SLA Countdown
                     ↓
Resolution & Spare Parts Cost Accounting
                     ↓
Audit Log & SLA Compliance Reporting
```

---

## 2. Facilities Asset Registry

Each physical facility on campus is tracked with comprehensive operational metadata:

- **Facility Types**: `ACADEMIC_BLOCK`, `CLASSROOM_BLOCK`, `LABORATORY`, `LIBRARY`, `AUDITORIUM`, `SEMINAR_HALL`, `SPORTS_COMPLEX`, `CAFETERIA`, `ADMINISTRATIVE_OFFICE`, `HOSTEL`, `PARKING_AREA`.
- **Operational Statuses**:
  - `ACTIVE`: Fully operational and bookable.
  - `UNDER_MAINTENANCE`: Temporarily restricted due to active maintenance work orders.
  - `INACTIVE` / `CLOSED`: Decommissioned or seasonal closure.
- **Embedded Equipment**: Linked high-value machinery, condition status (`EXCELLENT`, `GOOD`, `FAIR`, `NEEDS_REPAIR`), and last inspection timestamps.

---

## 3. Work Orders Desk & Priority Management

Work orders can originate from student complaints, staff reports, or scheduled facility inspections.

| Priority | SLA Target | Typical Scenarios | Automatic Escalation |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | **4 Hours** | Main power grid failure, gas leak, server room AC failure, structural hazard | Immediate SMS/Push to Chief Estate Engineer |
| **HIGH** | **12 Hours** | Floor water leakage, classroom audio system down, network switch malfunction | Alert after 6 hours elapsed |
| **MEDIUM** | **24 Hours** | Individual lighting fixture out, door handle damaged, whiteboard replacement | Daily warden digest |
| **LOW** | **48 Hours** | Cosmetic painting touch-ups, routine gardening, non-critical window latch | Standard queue |

---

## 4. Work Order Status Transitions & Cost Accounting

```text
REQUESTED → ASSIGNED → IN_PROGRESS → ON_HOLD → RESOLVED → CLOSED
                                          ↓
                                      CANCELLED
```

### Complete Audit Record:
- Every status transition logs `fromStatus`, `toStatus`, `timestamp`, `changedBy`, and detailed operational `notes`.
- Upon resolution, technicians document `resolutionSummary` and `actualCostInr`, enabling estate managers to analyze actual vs. estimated repair budgets.
