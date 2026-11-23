# CampusOS Documentation Migration Plan

**Status:** approved and implemented; 79 documents moved and known README/runbook links updated
**Scope:** the 79 Markdown files directly inside `docs/`
**Parent audit:** [Repository Structure Audit](file-structure-audit.md)

## Recommendation

Keep the existing top-level documentation areas (`ai`, `api`, `architecture`, `backend`, `campus`, `database`, `decisions`, `deployment`, `frontend`, `product`, `security`, and `ux`). Add `docs/operations/` for operator and domain runbooks, which currently have no clear home. Retain separate documents when they cover different audiences or layers; organize them together, but do not merge by filename or subject alone.

The target names below avoid overwriting an existing file with the same path. These destinations were applied after approval. The new `docs/operations/` folder was created for operational runbooks.

## Exact proposed path mapping

| Current path | Proposed target path | Review note |
|---|---|---|
| `docs/accreditation-quality-assurance-operations.md` | `docs/operations/accreditation-quality-assurance.md` | Institutional operations runbook. |
| `docs/adoption-guidance-operations.md` | `docs/operations/adoption-guidance.md` | Adoption and training operations. |
| `docs/ai-architecture.md` | `docs/ai/architecture-and-safety.md` | Distinct from existing `docs/ai/architecture.md`; compare coverage and cross-link rather than overwrite. |
| `docs/analytics.md` | `docs/backend/analytics-engine.md` | Distinct from `docs/backend/analytics-platform.md`; compare overlap and decide canonical relationship. |
| `docs/api-authentication.md` | `docs/api/authentication.md` | API platform credential/authentication guide. |
| `docs/api-lifecycle.md` | `docs/api/lifecycle.md` | API consumer application lifecycle. |
| `docs/api-platform.md` | `docs/api/platform-architecture.md` | API platform architecture. |
| `docs/api-rate-limits.md` | `docs/api/rate-limits.md` | API limits and quotas. |
| `docs/api-scopes.md` | `docs/api/scopes.md` | Capability scopes. |
| `docs/api-security.md` | `docs/api/security.md` | API-specific security, separate from general platform security. |
| `docs/api-versioning.md` | `docs/api/versioning.md` | API versioning policy. |
| `docs/audit.md` | `docs/security/audit-logging.md` | Forensic audit-log design; cross-link database audit model. |
| `docs/authentication.md` | `docs/security/authentication-architecture.md` | General authentication architecture. |
| `docs/backup-restore.md` | `docs/deployment/backup-restore.md` | Backup and restore runbook. |
| `docs/campus-security-visitor-access-emergency-operations.md` | `docs/operations/campus-security-visitor-access-emergency.md` | Campus operations runbook. |
| `docs/campus-sustainability-energy-carbon-intelligence-operations.md` | `docs/operations/campus-sustainability-energy-carbon-intelligence.md` | Campus operations manual. |
| `docs/certificates.md` | `docs/backend/certificate-engine.md` | Certificate engine and digital credentials. |
| `docs/data-import-migration-operations.md` | `docs/operations/data-import-migration.md` | Data import/migration operations. |
| `docs/deployment.md` | `docs/deployment/production-deployment.md` | README currently links to the old path; update it in the same approved change. |
| `docs/developer-api.md` | `docs/api/developer-portal.md` | Developer API reference/portal. |
| `docs/disaster-recovery-runbooks.md` | `docs/deployment/disaster-recovery-runbooks.md` | Operational runbooks; keep separate from the plan. |
| `docs/disaster-recovery.md` | `docs/deployment/disaster-recovery-plan.md` | Disaster recovery plan; README currently links to the old path. |
| `docs/document-storage.md` | `docs/backend/document-storage.md` | Storage architecture and file security. |
| `docs/documents.md` | `docs/backend/documents-engine.md` | Backend engine architecture; distinct from `docs/frontend/documents.md`. |
| `docs/domain-events.md` | `docs/backend/domain-events.md` | Domain event design. |
| `docs/environment-configuration.md` | `docs/deployment/environment-configuration.md` | Configuration strategy; README currently links to the old path. |
| `docs/hostel-residential-life-operations.md` | `docs/operations/hostel-residential-life.md` | Residential operations. |
| `docs/identity-provider-operations.md` | `docs/operations/identity-provider.md` | Operator procedures for identity providers. |
| `docs/identity-provisioning.md` | `docs/security/identity-provisioning.md` | Identity lifecycle/security design. |
| `docs/identity.md` | `docs/security/identity-architecture.md` | Identity architecture. |
| `docs/incident-response.md` | `docs/security/incident-response.md` | README currently links to the old path. |
| `docs/infrastructure.md` | `docs/deployment/production-infrastructure.md` | Production infrastructure architecture; README currently links to the old path. |
| `docs/integration-marketplace-operations.md` | `docs/operations/integration-marketplace.md` | Integration operations. |
| `docs/intelligence-api.md` | `docs/api/intelligence-api.md` | API reference; avoid confusion with intelligence architecture docs. |
| `docs/intelligence.md` | `docs/backend/intelligence-engine.md` | Backend intelligence engine; distinct audience from `docs/frontend/intelligence.md`. |
| `docs/international-relations-global-mobility-operations.md` | `docs/operations/international-relations-global-mobility.md` | International relations operations. |
| `docs/knowledge-base-policy-operations.md` | `docs/operations/knowledge-base-policy.md` | Knowledge/policy operations. |
| `docs/legal-operations-contract-compliance-risk.md` | `docs/operations/legal-contract-compliance-risk.md` | Legal operations. |
| `docs/library-learning-resources-operations.md` | `docs/operations/library-learning-resources.md` | Library operations. |
| `docs/metrics.md` | `docs/backend/metric-definitions.md` | Business metric definitions; compare with existing governed metric registry. |
| `docs/mfa.md` | `docs/security/multi-factor-authentication.md` | Authentication security. |
| `docs/multi-tenancy.md` | `docs/database/multi-tenancy-architecture.md` | Distinct from existing `docs/database/multi-tenancy.md`; compare and cross-link. README links to the old path. |
| `docs/observability.md` | `docs/deployment/observability.md` | Runtime observability. |
| `docs/oidc.md` | `docs/security/oidc-integration.md` | Identity protocol integration. |
| `docs/outbox-pattern.md` | `docs/backend/outbox-pattern.md` | Distinct from existing `docs/backend/transactional-outbox.md`; compare overlap and link. |
| `docs/payroll-compensation-statutory-compliance-operations.md` | `docs/operations/payroll-compensation-statutory-compliance.md` | Payroll operations. |
| `docs/performance-engineering.md` | `docs/deployment/performance-engineering.md` | Performance and capacity operations. |
| `docs/platform-operations.md` | `docs/operations/platform-administration.md` | SaaS/platform administration runbook. |
| `docs/procurement-vendor-inventory-operations.md` | `docs/operations/procurement-vendor-inventory.md` | Procurement operations. |
| `docs/production-security-checklist.md` | `docs/security/production-checklist.md` | README currently links to the old path. |
| `docs/quality-engineering.md` | `docs/architecture/quality-engineering.md` | Engineering standards and quality process. |
| `docs/records-lifecycle-retention-operations.md` | `docs/operations/records-lifecycle-retention.md` | Records operations. |
| `docs/release-certification.md` | `docs/deployment/release-certification.md` | Release process/certification. |
| `docs/report-exports.md` | `docs/backend/report-exports.md` | Backend export behavior and controls. |
| `docs/report-security.md` | `docs/security/report-security.md` | Report data security. |
| `docs/reporting.md` | `docs/backend/reporting-architecture.md` | Backend reporting architecture. |
| `docs/research-collaboration-grants-portfolio-operations.md` | `docs/operations/research-collaboration-grants-portfolio.md` | Research operations. |
| `docs/research-innovation-grants-operations.md` | `docs/operations/research-innovation-grants.md` | Research operations. |
| `docs/scheduled-jobs.md` | `docs/backend/scheduled-jobs.md` | Scheduler/job behavior and operation. |
| `docs/security-operations-runbooks.md` | `docs/operations/security-operations-runbooks.md` | Security operations procedures; distinct from security architecture. |
| `docs/security-threat-model.md` | `docs/security/threat-model.md` | Threat model. |
| `docs/security.md` | `docs/security/hardening-guide.md` | Distinct from `docs/security/architecture.md`; README currently links to the old path. |
| `docs/service-desk-runbooks.md` | `docs/operations/service-desk.md` | Service desk procedures. |
| `docs/session-security.md` | `docs/security/session-security.md` | Session security. |
| `docs/sports-athletics-recreation-management-operations.md` | `docs/operations/sports-athletics-recreation.md` | Sports operations. |
| `docs/sso.md` | `docs/security/single-sign-on.md` | Single sign-on. |
| `docs/student-admissions-enrollment-operations.md` | `docs/operations/student-admissions-enrollment.md` | Admissions operations. |
| `docs/student-affairs-grievance-disciplinary-operations.md` | `docs/operations/student-affairs-grievance-disciplinary.md` | Student affairs operations. |
| `docs/student-counselling-mentoring-development-operations.md` | `docs/operations/student-counselling-mentoring-development.md` | Student support operations. |
| `docs/student-engagement-community-service-operations.md` | `docs/operations/student-engagement-community-service.md` | Engagement operations. |
| `docs/student-housing-off-campus-accommodation-operations.md` | `docs/operations/student-housing-off-campus-accommodation.md` | Housing operations. |
| `docs/student-success-advising-operations.md` | `docs/operations/student-success-advising.md` | Student success operations. |
| `docs/subscription-customer-success-operations.md` | `docs/operations/subscription-customer-success.md` | SaaS customer success operations. |
| `docs/tenant-onboarding-runbooks.md` | `docs/operations/tenant-onboarding.md` | Tenant onboarding runbooks. |
| `docs/timetable-resource-scheduling-operations.md` | `docs/operations/timetable-resource-scheduling.md` | Timetable operations. |
| `docs/transport-fleet-routes-mobility-operations.md` | `docs/operations/transport-fleet-routes-mobility.md` | Transport operations. |
| `docs/workflow-engine.md` | `docs/backend/workflow-engine.md` | Engine architecture; compare with backend workflow docs. |
| `docs/workflows.md` | `docs/backend/enterprise-workflows.md` | Distinct from existing `docs/backend/workflows.md`; compare and link. |
| `docs/workforce-staff-lifecycle-leave-operations.md` | `docs/operations/workforce-staff-lifecycle-leave.md` | Workforce operations. |

## Similar-topic review before any move

These pairs or groups have related subjects but are not established duplicates. Keep both unless content review demonstrates a safe consolidation:

- `docs/ai-architecture.md` and `docs/ai/architecture.md` — different titles and emphases (safety boundary vs intelligence layer).
- `docs/multi-tenancy.md`, `docs/database/multi-tenancy.md`, and `docs/database/multi-tenancy-strategy.md` — architecture, database implementation, and strategy may overlap.
- `docs/documents.md`, `docs/document-storage.md`, and `docs/frontend/documents.md` — engine, storage/security, and frontend module guidance.
- `docs/workflows.md`, `docs/workflow-engine.md`, and `docs/backend/workflows.md` — broad workflow automation, engine architecture, and backend workflow notes.
- `docs/security.md`, `docs/security/architecture.md`, `docs/api-security.md`, and `docs/report-security.md` — platform, API, and reporting security layers.
- `docs/analytics.md`, `docs/backend/analytics-platform.md`, `docs/metrics.md`, `docs/backend/metric-registry.md`, and `docs/reporting.md` — analytics, metrics, reporting, and exports.
- `docs/outbox-pattern.md` and `docs/backend/transactional-outbox.md` — likely related; compare design vs implementation/reliability coverage.
- `docs/intelligence.md`, `docs/frontend/intelligence.md`, `docs/ai-architecture.md`, and `docs/ai/architecture.md` — keep audience/layer distinctions clear.

The comparison above used headings and file placement to identify review candidates. It is not a full content merge analysis.

## Known links and migration checks

`README.md` linked to several root-level files that changed path. Those references were updated. The production deployment guide's invalid `file:///docs/disaster-recovery.md` link was changed to a relative Markdown link to the moved disaster recovery plan.

The files were moved with Git-aware renames; document contents were not consolidated or rewritten. The moved targets and the README/runbook references listed above were checked. A broader relative-link scan also found four pre-existing links in `docs/campus/README.md` pointing to absent `clubs.md`, `announcements.md`, `notifications.md`, and `audience-targeting.md`; these are unrelated to this move and remain unresolved. No application code, routes, APIs, or migrations were changed.

## Scope boundary

This approval covered only the documentation moves listed above and their links. It did not authorize frontend/backend code moves or merging any documents.
