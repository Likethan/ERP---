# Intelligence Domain (`app/domains/intelligence`)

## Purpose

Provides institutional business intelligence, administrative analytics dashboards, audit trail logging, and permission-governed AI assistant tools.

## Key Entities

- `AnalyticsSnapshot`
- `AuditTrailEntry`
- `AIAssistantTool`
- `AIQueryAudit`

## Boundaries & Constraints

- AI tools must execute strictly through authorized domain service calls; direct SQL generation or unfiltered database execution is prohibited.
- Analytics aggregations are computed asynchronously or read from dedicated materialized views to prevent load on operational tables.
