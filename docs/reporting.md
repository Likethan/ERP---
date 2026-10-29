# CampusOS Enterprise Reporting Layer

## Overview
CampusOS provides an enterprise-grade, multi-tenant reporting architecture designed for institutional accountability, statutory compliance, and operational decision-making. The reporting framework is built on a controlled query specification model that completely prevents arbitrary SQL execution, enforces tenant isolation at the query planner level, and maintains reproducible versioned reporting semantics.

## Architecture
```text
                     CampusOS Client / UI
                              │
                              ▼
                     REST API & PBAC Check
                              │
                              ▼
                 Query Specification Validation
              (Dataset / Dimension / Measure Checks)
                              │
                              ▼
                    Tenant-Partitioned Cache
                              │
                  ┌───────────┴───────────┐
             Cache Hit               Cache Miss
                  │                       │
                  ▼                       ▼
            Normalized DTO        Reporting Engine
                                  (SQLAlchemy ORM / Core)
                                          │
                                          ▼
                                 Result Normalization
                        j                  │
                        ┌─────────────────┼─────────────────┐
                        ▼                 ▼                 ▼
                    Chart Series      Table Rows        Forensic Audit
```

## Core Features
1. **Approved Datasets & Measures**: Only pre-registered datasets (`students`, `faculty`, `attendance`, `examinations`, `finance`, `placement`, `campus_events`, `infrastructure`, `documents`, `cross_domain_student_success`) can be queried.
2. **Deterministic Versioning**: Modifying a report query specification automatically bumps the version number, preserving historical version snapshots without altering previously executed report semantics.
3. **Role-Aware Scoping**: Student accounts are automatically scoped to their personal enrollment records; faculty accounts are restricted to their assigned courses and departmental cohorts.
4. **Forensic Auditability**: Every report creation, modification, execution, export, and download is permanently recorded in the forensic audit ledger.