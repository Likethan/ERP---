# CampusOS Repository Structure Audit

**Status:** proposal only; no application files moved, renamed, deleted, or rewritten
**Audited baseline:** `develop` at `cf58345` (`feat(ui): modernize college ERP UI with clean white-and-yellow theme and database utilities`), before the approved documentation and app-folder moves
**Scope:** tracked repository layout and source/config placement, with static path/reference inspection. This is not a code-quality, security, route-contract, or runtime audit.

## Working-tree preservation

The checkout already contains uncommitted changes in:

- `frontend/src/app/app/layout.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/app/login/page.tsx`
- `frontend/src/components/dashboard/admin-dashboard.tsx`
- `frontend/src/components/navigation/sidebar.tsx`
- `frontend/src/components/navigation/topbar.tsx`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/card.tsx`
- `frontend/src/components/ui/stat-card.tsx`
- `frontend/src/components/ui/table.tsx`
- untracked `frontend/src/app/admin/`

These are pre-existing user changes and are outside this proposal. The audit was read-only against application files. No tests or builds were run.

## Executive assessment

The repository now keeps the web application in root `frontend/` and the Python API in root `backend/`, as approved. This audit records the pre-move baseline; its findings about organization inside those app boundaries still apply. npm workspaces cover `frontend` and shared `packages/*`; the API remains a separate Python project. The documentation move is recorded in `documentation-migration-plan.md`.

The highest-value future work is to establish one canonical home for each domain's backend and frontend code, consolidate duplicate-looking names only after behavior and ownership are verified, and bring root operational artifacts into predictable `scripts/`, `data/`, `docs/`, and `deploy/` locations. Keep Next.js route files at their current route paths unless intentionally changing public URLs; keep Alembic revision identities and ordering intact.

## Evidence and findings

### 1. Monorepo boundaries: good foundation; root scripts need scope clarity

- Root `package.json` declares workspaces for `frontend` and `packages/*`; `frontend/package.json` owns Next.js dependencies and scripts.
- `backend/pyproject.toml` and API requirements files own Python configuration; the API has `app/`, `migrations/`, and `tests/`.
- Shared code is already represented by `packages/types` and `packages/config`.
- Root `requirements.txt` duplicates API runtime requirements, while `backend/requirements-dev.txt` includes the API requirements. Root and API Python install paths therefore need an explicit policy to avoid drift.
- Root npm `format` scripts traverse `**/*` and do not visibly exclude generated/vendor trees; `.prettierignore` may mitigate this, but the command's scope is broader than the app/package workspace model.

**Assessment:** retain root manifests, lockfile, Docker Compose files, `.gitignore`, and shared packages. Clarify whether root Python requirements are a supported install entry point or a compatibility wrapper before removing or relocating them.

### 2. Backend domain boundaries are partial and parallel

`backend/app/` contains several competing organizations:

- `api/v1/` has a broad collection of domain routers.
- `models/`, `schemas/`, and `services/` are broad shared directories, each containing many domain-specific modules.
- `domains/` exists, but most domain folders contain only a README; implementation is concentrated in `domains/intelligence/` and some supporting subpackages.
- `identity/`, `integrations/`, `platform_api/`, `repositories/`, and `core/` are additional top-level boundaries.

Representative evidence: `api/v1/finance.py`, `models/finance.py`, `schemas/finance.py`, and `services/finance_service.py` describe one domain across four layers; `domains/finance/` currently has a README rather than those implementations. `main.py`/`api/v1/router.py` are the composition boundary, and route modules import from `app.services` or `app.domains`.

**Risk:** developers cannot infer the authoritative domain implementation from the directory tree. Moving code indiscriminately into `domains/` risks circular imports and breaks import strings, Alembic metadata registration, background jobs, and test fixtures.

**Recommendation:** converge gradually on domain packages, but first map imports and define dependency direction: API/router → application service → domain model/repository → core/shared primitives. Cross-domain calls should use narrow service interfaces/events; domains should not import API routers. Keep `core/` limited to cross-cutting infrastructure, not domain workflows.

### 3. Frontend has a large service bucket and ambiguous module ownership

- `frontend/src/services/` contains dozens of module APIs and calculators side by side, plus an `index.ts` re-export surface.
- `components/` is partly domain-grouped (`documents`, `housing`, `student-support`, etc.) but also has broad `dashboard`, `navigation`, and `ui` buckets.
- `types/` and `mocks/` are flat domain-wide directories; `lib/` contains cross-cutting API/auth/utilities.
- `app/` correctly owns Next.js routes. It should remain the routing layer, with business UI/data logic imported from feature modules.

Concrete naming ambiguity: `placement.service.ts` and `placements.service.ts` both exist, both are exported from `services/index.ts`, and the former is used by many placement route pages while the latter is used by dashboards. The matching `placement.mock.ts` and `placements.mock.ts` are also separate imports. This proves split ownership and naming inconsistency, but not identical behavior; do not merge until their contracts and consumers are compared.

**Recommendation:** introduce `src/features/<domain>/` ownership for domain UI, API/service, types, and mock data. Keep shared `src/components/ui`, `src/lib`, and `src/app` for truly shared primitives, cross-cutting utilities, and route composition. Preserve route segment paths while moving imported implementation behind them.

### 4. Frontend test placement/config is inconsistent

- API tests are grouped in `backend/tests/`, matching `pyproject.toml`'s `testpaths = ["tests"]`.
- Web unit-style tests are under `frontend/src/__tests__/`.
- Browser journeys are under `frontend/e2e/` with `frontend/playwright.config.ts`.
- `frontend/tsconfig.json` excludes `src/__tests__` and `e2e`, so those tests do not participate in the web app's normal TypeScript project.

**Recommendation:** standardize web test ownership as `frontend/tests/unit/` and `frontend/tests/e2e/` (or retain `e2e/` but document the distinction), and add an explicit test TypeScript config/runner. Keep API tests in `backend/tests/`. Do not relocate any tests until the active test runner and discovery patterns are confirmed.

### 5. Documentation layout contradicts the repository guide

The README's repository tree describes topic-specific subfolders under `docs/` (architecture, API, database, security, deployment, etc.), and many such directories exist. Yet dozens of operational and technical markdown files remain directly under `docs/`, including `deployment.md`, `documents.md`, `security.md`, `multi-tenancy.md`, `workflows.md`, and many domain operations runbooks. There are also same-basename docs in different locations, such as `docs/documents.md` and `docs/frontend/documents.md`, and root-vs-topic pairs such as `docs/multi-tenancy.md` and `docs/database/multi-tenancy.md`.

**Risk:** duplicate titles and flat placement make the canonical guidance unclear; filename matches alone do not prove duplicate content.

**Recommendation:** make the README's topic layout authoritative, establish canonical docs for each subject, and use redirects or an index for renamed docs if external links may exist. Compare content and inbound links before merging any same-topic docs.

### 6. Root operational artifacts need clearer homes

- Root `scripts/` contains developer automation and operational Python/PowerShell/shell scripts.
- Root also contains multiple student utility `.bat` wrappers (`add_student.bat`, `import_students.bat`, `view_students.bat`) beside app manifests.
- Root `data/students_roster.csv` is a sample/operational data input, but its purpose and handling are not stated by its path.
- Generated-looking reports `accessibility_report.json`, `e2e_validation_report.json`, `release_readiness_report.json`, and `release_readiness_report.md` sit at repository root.
- Deployment files are split between root Compose manifests and `deploy/nginx/`.

**Recommendation:** categorize scripts by purpose/platform; put generated reports under an ignored `artifacts/reports/` output location; classify the CSV as synthetic fixture, import sample, or sensitive institutional data before choosing `data/fixtures/` or a private external location. Keep production/runtime config separate from generated outputs. Preserve current script entry points until all docs, CI, and operator workflows are updated.

### 7. Duplicate-module and dependency/cycle risks

The audit identifies **candidate overlaps**, not confirmed duplicate implementations:

- Backend policy services: `app/services/policy_service.py`, `app/identity/policy_service.py`, and `app/domains/intelligence/governance/policy_service.py`.
- Backend analytics services: `app/services/analytics_service.py` and `app/domains/intelligence/services/analytics_service.py`.
- Frontend placement service/mock pairs: singular and plural files noted above.
- Related transport, hostel, and document service files are split between broad aggregate services and narrower resource services.

The tree and selected import references show routes importing across these parallel layers, but a full automated import graph/cycle analysis was not run. Circular-import risk is therefore **unverified**, not a confirmed defect. It is elevated during migration because `main.py`, router aggregation, model registration, schema references, worker/scheduler imports, and broad barrel exports are composition points.

**Required before moving code:** generate Python and TypeScript dependency graphs, record current import edges and public exports, identify dynamic imports/string-based references, and inspect Alembic `env.py` imports/model discovery. Avoid broad `__init__.py` re-exports that create cycles.

## Proposed target structure

The root-level `frontend/` and `backend/` paths below reflect the approved folder move. The internal feature/domain organization remains the proposed target:

```text
CampusOS/
├── frontend/
│   ├── src/app/                    # Next.js route tree; preserve URL segments
│   ├── src/features/<domain>/      # Domain UI, services, types, mocks
│   ├── src/components/ui/          # Shared design primitives
│   └── tests/{unit,e2e}/            # Explicit unit and browser test suites
├── backend/
│   ├── app/
│   │   ├── api/v1/                    # HTTP adapters and versioned routes
│   │   ├── core/                      # Cross-cutting config, DB, auth, observability
│   │   ├── domains/<domain>/          # Domain model, schemas, repository, services
│   │   ├── identity/                  # Identity-provider/session subsystem
│   │   ├── integrations/              # External-system adapters
│   │   └── platform_api/              # SaaS platform API boundary
│   ├── migrations/                    # Immutable Alembic revision history
│   └── tests/                         # API tests
├── packages/{types,config}/            # Stable shared packages
├── docs/{product,architecture,api,database,security,ux,deployment,operations,decisions}/
├── scripts/{dev,ops,windows}/           # Maintained entry points by purpose/platform
├── data/fixtures/                       # Only synthetic, non-sensitive test data
├── artifacts/reports/                   # Generated, ignored output
├── deploy/nginx/                        # Existing proxy configuration
├── docker-compose*.yml                  # Existing orchestration entry points
└── package.json / package-lock.json     # Workspace root and single npm lockfile
```

Backend domain extraction should be incremental: choose one bounded domain, move its model/schema/service/repository behind a domain package, retain thin legacy import shims temporarily where needed, then remove shims only after consumers and deployment entry points are migrated. Some cross-cutting services should stay under `core/`, `identity/`, or `integrations/`; not every file belongs in a business domain.

## Current path → proposed target path

The mappings below are path-level proposals for a later internal reorganization. Wildcards mean all files matching the stated current directory/file pattern; exact files and imports must be inventoried before any such move.

| Current path | Proposed target | Notes / gate |
|---|---|---|
| `backend/app/models/<domain>.py` | `backend/app/domains/<domain>/models.py` | Per-domain pilot only; update `models/__init__.py`, Alembic discovery, relationship imports, and tests together. |
| `backend/app/schemas/<domain>.py` | `backend/app/domains/<domain>/schemas.py` | Preserve serialization/API schemas and compatibility imports. |
| `backend/app/services/<domain>_service.py` | `backend/app/domains/<domain>/service.py` | Only domain-owned services; keep cross-cutting helpers in `core/` or dedicated subsystem. |
| `backend/app/api/v1/<domain>.py` | `backend/app/api/v1/<domain>.py` | **No route-file move proposed initially**; maintain stable OpenAPI and URL contracts. Later package routers only if justified. |
| `frontend/src/services/<domain>.service.ts` and `<domain>-*.service.ts` | `frontend/src/features/<domain>/api/` | Require import graph, public export inventory, and a domain-by-domain migration. Resolve singular/plural placement ownership first. |
| `frontend/src/types/<domain>.ts` | `frontend/src/features/<domain>/types.ts` | Shared cross-domain contracts remain in `packages/types` or a documented shared type module. |
| `frontend/src/mocks/<domain>.mock.ts` | `frontend/src/features/<domain>/mocks/` | Verify mock-only vs runtime fallback usage and eliminate ambiguous duplicate ownership only after diff/consumer review. |
| `frontend/src/components/<domain>/**` | `frontend/src/features/<domain>/components/` | Keep shared `ui`, `navigation`, and genuinely shared dashboard components in `components/`. |
| `frontend/src/__tests__/*.test.ts` | `frontend/tests/unit/` | Update Vitest/Jest/other runner discovery and TS config if present; runner not confirmed by this audit. |
| `frontend/e2e/**` | `frontend/tests/e2e/**` | Optional consolidation; update Playwright config paths and CI commands together. |
| `docs/*.md` | Topic-specific `docs/{architecture,api,database,security,deployment,backend,frontend,campus}/` | Assign each file individually using subject and canonical-content review; do not blindly move all flat docs to one folder. |
| `scripts/*.py`, `scripts/*.ps1`, `scripts/*.sh`, `scripts/*.mjs` | `scripts/{ops,dev}/` | Categorize by operator vs developer workflow; update README, package scripts, CI, and runbooks. |
| `add_student.bat`, `import_students.bat`, `view_students.bat` | `scripts/windows/` | Update all references and test on Windows; keep compatibility wrappers if operators depend on root paths. |
| `data/students_roster.csv` | `data/fixtures/students_roster.csv` **if synthetic** | If real/sensitive data, do not put in Git; move only via approved data-handling process. Determine provenance first. |
| `accessibility_report.json`, `e2e_validation_report.json`, `release_readiness_report.json`, `release_readiness_report.md` | `artifacts/reports/` | Confirm generation commands and whether any are checked-in source-of-truth records; add ignore/output policy before relocating. |
| `requirements.txt` (root) | Remain at root as documented compatibility manifest, or remove only after approval and consumer inventory | It duplicates API runtime dependencies; do not move/delete until CI/deploy/operator references are known. |
| `docker-compose.yml`, `docker-compose.prod.yml`, root workspace manifests | Remain at root | These are repository entry points and should not be nested without a compelling deployment change. |
| `backend/migrations/**` | Remain at `backend/migrations/**` | Never rename/reorder existing revisions as part of structural cleanup. |

## Safe migration plan (approval required before implementation)

1. **Freeze the baseline.** Record branch/head and preserve the existing uncommitted UI changes. Use a clean worktree or a narrowly scoped branch for any approved moves.
2. **Inventory references.** Search source, tests, scripts, Dockerfiles/Compose, CI workflows, docs, IDE configs, and packaging for every proposed path; include dynamic imports, Python dotted paths, environment settings, and route strings.
3. **Baseline behavior.** Identify the supported build, lint, unit, API, browser, migration, and deployment commands. Capture current OpenAPI paths, Next route paths, Alembic revision graph, and generated artifacts before edits.
4. **Define boundaries.** Approve one target taxonomy and ownership rules for domain code, shared types/config, test suites, fixtures, generated reports, and operational scripts.
5. **Pilot a low-risk slice.** Start with one frontend domain or a docs/script-only move. Use Git moves; update imports/config/docs atomically. Do not combine route/API behavior changes with structural moves.
6. **Verify each slice.** Run the agreed checks, compare route/API/schema/migration snapshots, inspect import cycles, check case-sensitive path behavior, and review the diff for content changes. Keep compatibility shims if downstream consumers remain.
7. **Expand by domain.** Migrate one vertical domain at a time, with separate reviewable commits. Never rewrite Alembic revision contents or IDs to make the new tree look uniform.
8. **Remove compatibility layers only after evidence.** Require zero old-path references in repository/CI/deploy and confirmation that external consumers are not using them.

## Approval boundary

The root-level `frontend/` and `backend/` move and the documentation move were approved and completed. The proposed internal domain reorganization remains a recommendation and needs its own reviewed migration plan before implementation.

## Audit limitations

- Inspected the repository tree, root/web/API manifests, Python configuration, README structure, selected route/service imports, relevant mocks/services, and Git status/head.
- Did not inspect every file's behavior or establish semantic duplication from filename matches.
- Did not run tests/builds or generate complete language-level dependency graphs.
- No files under the project mirror's `sources/` reference directory were edited; the application tree is under `CampusOS/`.
