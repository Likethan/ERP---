# Campus Domain (`app/domains/campus`)

## Purpose

Manages student clubs, collegiate organizations, campus-wide events, institutional circulars, and system notifications.

## Key Entities

- `Club`
- `ClubMembership`
- `CampusEvent`
- `EventRegistration`
- `InstitutionalAnnouncement`
- `Notification`

## Boundaries & Constraints

- Dispatches targeted notifications to specific roles, departments, or sections defined in Core and People domains.
