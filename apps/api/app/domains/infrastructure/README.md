# Infrastructure Domain (`app/domains/infrastructure`)

## Purpose

Coordinates physical campus resources including hostel dormitories, room allocations, transport vehicle fleets, and bus routes.

## Key Entities

- `HostelBuilding`
- `HostelRoom`
- `BedAllocation`
- `TransportRoute`
- `Vehicle`
- `RouteStop`
- `TransportPass`

## Boundaries & Constraints

- Binds allocations directly to `people_students.id` or `people_staff.id`.
- Communicates fee requirements to the Finance domain for room rent and bus pass billing.
