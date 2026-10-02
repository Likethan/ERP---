# CampusOS — Campus Transport, Fleet & Student Boarding Pass Workflows

## 1. Overview

The CampusOS Transport logistics module manages institutional bus routes, pick-up stops, commercial fleet vehicles, certified drivers, and student bus boarding pass allocations.

```text
Route & Pick-up Stop Network
            ↓
Vehicle Fleet & Driver Assignment
            ↓
Student Pass Allocation & Seat Booking
            ↓
Daily Commute Dispatch & Tracking
            ↓
Pass Relocation / Cancellation Workflow
```

---

## 2. Bus Routes & Stops Hierarchy

Each route is an ordered sequence of designated boarding stops connecting regional city nodes to the institutional campus gates:

- **Route Attributes**: Route Code (`R-01`), Title, Morning Departure Time (`07:15 AM`), Evening Return Time (`05:15 PM`), Vehicle Number, Driver Contact.
- **Stop Sequence**: Numbered from 1 (origin) to N (final campus arrival). Each stop records landmark details and student boarding counts.
- **Capacity Utilization**: Evaluated continuously against assigned vehicle seating. If allocation reaches 90%+, capacity warning badges are displayed to prevent student overcrowding.

---

## 3. Fleet Maintenance & Fitness Tracking

Institutional passenger safety mandates strict regulatory compliance for all transport vehicles:

1. **Fleet Classifications**: Buses (52–54 seaters), Mini-Buses (32 seaters), Vans (14 seaters), Utility vehicles.
2. **Fuel Types**: Diesel, Compressed Natural Gas (CNG), Electric (EV), Petrol.
3. **Regulatory Inspection Dates**:
   - **Fitness Certificate Validity**: Monitored by real-time countdown alerts.
   - **Comprehensive Insurance Expiry**: Automatic flag if expiring within 30 days.
   - **Status Transitions**: `AVAILABLE` → `ACTIVE` → `MAINTENANCE` → `OUT_OF_SERVICE`.

---

## 4. Driver Profiles & Regulatory Licensing

- **License Verification**: Commercial Heavy Motor Vehicle (HMV/Transport) license validation with expiry warnings.
- **Badge Authentication**: State transport authority commercial badge registration.
- **Route Association**: Primary route and secondary emergency standby assignments.

---

## 5. Student Transport Pass Allocation Workflow

```text
Student Selects Route & Preferred Pick-Up Stop
                    ↓
System Checks Remaining Seat Capacity
                    ↓
Pass Created (Status: ACTIVE, Seat Assigned)
                    ↓
Finance Clearance Linked (Fee Status: PAID / PENDING)
                    ↓
Digital Boarding Pass Generated with Route Schedule
                    ↓
Optional Pass Cancellation (Hostel Relocation / Withdrawal)
```
