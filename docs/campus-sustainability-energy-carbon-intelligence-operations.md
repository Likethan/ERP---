# CampusOS — Campus Sustainability, Energy Management, Environmental Compliance & Carbon Intelligence Operations Manual (Step 67)

**Product:** CampusOS — “One Campus. One System. One Source of Truth.”  
**Module:** Enterprise Campus Sustainability & Carbon Intelligence Platform  
**Release Version:** CampusOS v67.0 (Enterprise Suite)  
**Security Classification:** Highly Confidential / Institutional Operations & Statutory Compliance  

---

## 1. Executive Summary & Purpose

The **Enterprise Campus Sustainability, Energy Management, Environmental Compliance & Carbon Intelligence Platform** (Step 67) empowers higher education institutions to transform campus operations into verified, climate-resilient, and statutory-compliant environments.

Rather than relying on disjointed spreadsheets or unverified sustainability claims, CampusOS establishes a single, auditable source of truth for:
1. **Multi-Source Energy Telemetry**: High-precision monitoring of utility grid feeds, rooftop/ground-mount solar PV arrays, diesel generator backup systems, and campus heating/boiler fuels with automated peak load anomaly detection.
2. **Water Resource Balance & Leak Mitigation**: Deep tracking of municipal supply, groundwater extraction (CGWA-compliant borewells), rainwater harvesting storage, and Sewage Treatment Plant (STP) greywater recycling loops, backed by automated dispatch of emergency maintenance work orders.
3. **Circular Waste Management & Hazardous TSDF Compliance**: Segregated tracking across municipal compostable organics (aerobic/vermicomposting), recyclables, e-waste Extended Producer Responsibility (EPR) recycling partners, and legally binding hazardous chemical/laboratory waste manifests (Form 10 / State Pollution Control Board TSDF consignments).
4. **Verifiable GHG Protocol Carbon Accounting (Scope 1, 2, 3)**: Rigorous emissions calculations tied directly to primary operational activity data and version-controlled emission factors (e.g., CEA CO2 Baseline Database v20.0, IPCC AR6 Guidelines). Every calculated period yields an immutable SHA-256 cryptographic audit digest.
5. **Decarbonization Capital Portfolio (ESG Initiatives)**: Institutional green capital investment tracking with capital budgets, operational expenditure, verified payback periods, and annualized avoided carbon metrics.
6. **Statutory Environmental Permitting & CAPA**: Full lifecycle oversight of State Pollution Control Board (SPCB) Consent to Operate (CTO/CTE), Central Ground Water Authority (CGWA) abstraction limits, biomedical/hazardous waste authorizations, and structured Corrective and Preventive Actions (CAPA).
7. **IoT Smart Meter Gateway & Telemetry Deduplication**: High-throughput telemetry ingestion endpoint protected by cryptographic device secret signatures, payload hash deduplication, and anomaly classification.
8. **Utility Invoice Batch Reconciliation**: CSV ingestion workflow for bulk billing records, verifying tariff variances, billing anomalies, and unmetered discrepancies against physical sub-meter readings.

---

## 2. Architecture & Domain Model

The sustainability module adheres strictly to the CampusOS multi-tenant enterprise framework, built with FastAPI, SQLAlchemy 2.0 async, Alembic migrations, and Next.js 15 App Router.

```
                           +-------------------------------------+
                           |   IoT Smart Meters / Modbus Gateway |
                           +------------------+------------------+
                                              | HTTPS / HMAC-SHA256
                                              v
+------------------------+        +---------------------------+        +--------------------------+
| Utility Invoices (CSV) |------->| Sustainability Service    |<-------| Building Sub-Meters /    |
| (Batch Reconciliation) |        | - Telemetry Deduplication |        | Manual Physical Logs     |
+------------------------+        | - Anomaly Detection (>30%)|        +--------------------------+
                                  | - GHG Protocol Engine     |
                                  +-------------+-------------+
                                                |
               +--------------------------------+-------------------------------+
               |                                |                               |
               v                                v                               v
+------------------------------+ +------------------------------+ +------------------------------+
|     Energy & Water Balance   | |  Circularity & TSDF Manifest | | Scope 1, 2, 3 GHG Calculator |
| - Grid / Solar / Genset kWh  | | - Organic Vermicomposting    | | - CEA Grid Baseline Factors  |
| - Borewell / STP Recycled kL | | - Hazardous Waste Form 10    | | - Cryptographic SHA-256 Hash |
| - Active Leak CAPA Workflow  | | - Authorized Recycler Certs  | | - Net-Zero Trajectory Model  |
+------------------------------+ +------------------------------+ +------------------------------+
               |                                |                               |
               +--------------------------------+-------------------------------+
                                                |
                                                v
                              +-----------------------------------+
                              |   Executive Composite ESG Hub     |
                              |   - Building EUI Heatmaps         |
                              |   - Statutory Compliance Rate (%) |
                              |   - Real-Time Decarbonization KPIs|
                              +-----------------------------------+
```

---

## 3. Database Schema & Migration Specifications

Database migration `049_enterprise_campus_sustainability_carbon_intelligence.py` establishes 12 core tables inheriting `TenantScopedModel` (`tenant_id`, `id`, `created_at`, `updated_at`, `is_active`):

| Table Name | Primary Purpose | Key Fields |
| :--- | :--- | :--- |
| `sustainability_profiles` | Campus master targets & baselines | `baseline_year`, `target_net_zero_year`, `carbon_reduction_target_pct`, `renewable_energy_target_pct`, `water_recycling_target_pct`, `coordinator_email` |
| `sustainability_targets` | Granular categorical KPIs | `category` (ENERGY, WATER, WASTE, EMISSIONS), `target_value`, `current_value`, `baseline_value`, `deadline_date`, `status` |
| `emission_factors` | Versioned GHG conversion registry | `factor_name`, `scope` (SCOPE_1, SCOPE_2, SCOPE_3), `activity_type`, `co2e_factor_kg_per_unit`, `source_name`, `effective_year`, `is_current` |
| `resource_measurements` | Energy, water, fuel meter readings | `resource_type`, `source_type`, `meter_identifier`, `quantity`, `unit`, `is_anomaly`, `anomaly_severity`, `reading_timestamp` |
| `water_incident_records` | Leakage & distribution defects | `incident_type`, `severity`, `status` (DETECTED, INVESTIGATING, REPAIRED, CLOSED), `estimated_loss_litres`, `remediation_notes` |
| `waste_records` | Waste circularity & TSDF manifests | `waste_category`, `disposal_method`, `quantity_kg`, `is_hazardous`, `tsdf_manifest_number`, `authorized_vendor_name`, `disposal_certificate_url` |
| `carbon_emissions_calculations` | Immutable GHG Protocol period audit | `reporting_period`, `scope_1_emissions_mt`, `scope_2_emissions_mt`, `scope_3_emissions_mt`, `total_emissions_mt`, `calculation_hash` (SHA-256) |
| `sustainability_initiatives` | Green capital decarbonization projects | `initiative_code`, `title`, `project_status`, `budget_allocated`, `annual_co2_reduction_mt`, `projected_annual_savings_inr`, `roi_payback_years` |
| `environmental_compliance_requirements` | Statutory permits (SPCB, CGWA) | `requirement_title`, `regulatory_body` (SPCB, CGWA, CPCB, MUNICIPAL), `permit_reference`, `expiry_date`, `compliance_status` |
| `environmental_corrective_actions` | Statutory CAPA remediation | `requirement_id`, `action_title`, `priority` (LOW, MEDIUM, HIGH, CRITICAL), `corrective_action_plan`, `closure_status`, `target_completion_date` |
| `iot_meter_streams` | Smart sub-meter identity & status | `meter_identifier`, `meter_type`, `modbus_address`, `device_secret`, `sampling_interval_seconds`, `last_heartbeat_at`, `status` |
| `iot_ingestion_events` | Telemetry logs with deduplication | `meter_id`, `payload_hash` (SHA-256), `raw_payload`, `ingestion_status` (PROCESSED, DUPLICATE, FAILED), `ingested_at` |
| `sustainability_import_batches` | Utility bill CSV imports | `batch_code`, `utility_provider`, `records_processed`, `records_failed`, `status` |

---

## 4. GHG Protocol Carbon Accounting Standards

CampusOS implements corporate carbon accounting following the **GHG Protocol Corporate Accounting and Reporting Standard**:

### 4.1 Scope Classification
1. **Scope 1 (Direct Emissions)**:
   - On-campus fuel combustion in diesel generators (backup power).
   - Institution-owned transport fleet (buses, ambulances, service vans).
   - Liquefied Petroleum Gas (LPG) and piped natural gas used in campus mess kitchens and laboratories.
   - Fugitive refrigerant leaks from campus central chillers and VRF systems.
2. **Scope 2 (Indirect Emissions — Grid Electricity)**:
   - Location-based accounting using CEA (Central Electricity Authority, India) CO2 baseline emission factors ($0.716\text{ kg CO}_2\text{e/kWh}$).
   - Market-based accounting factoring in institutional on-site solar self-consumption and green energy wheeling power purchase agreements (Open Access Solar).
3. **Scope 3 (Other Indirect Emissions)**:
   - Student and faculty daily commuting patterns.
   - Institutional air and rail business travel.
   - Municipal solid waste sent to landfills.
   - Water abstraction and off-site municipal wastewater treatment.

### 4.2 Cryptographic Audit Trail
To protect against greenwashing and regulatory audit non-compliance, every carbon calculation run generates a deterministic SHA-256 digest:
$$\text{Audit Hash} = \text{SHA256}(\text{TenantID} \parallel \text{Period} \parallel S_1 \parallel S_2 \parallel S_3 \parallel \text{Timestamp})$$
This hash is recorded in `carbon_emissions_calculations.calculation_hash` and printed on all executive ESG audit certificates.

---

## 5. Automated Peak Load & Consumption Anomaly Engine

Every resource measurement submitted via manual logging, utility invoice reconciliation, or IoT telemetry is processed through the real-time anomaly engine:

1. **Baseline Calculation**:
   - Compares the submitted reading against historical mean consumption for the corresponding meter or building over the preceding 30 days during equivalent operating hours.
2. **Variance Classification**:
   - $\text{Variance} = \frac{|\text{Reading} - \text{Expected}|}{\text{Expected}} \times 100\%$
   - $\text{Variance} \le 30.0\%$: `NORMAL` severity; no alert triggered.
   - $30.0\% < \text{Variance} \le 50.0\%$: `WARNING` severity; flagged on energy dashboard; maintenance inspection notification dispatched.
   - $\text{Variance} > 50.0\%$: `CRITICAL` severity; triggers emergency operational alert; automatically opens a maintenance work order in the campus facilities module.

---

## 6. Circular Waste & Hazardous TSDF Compliance

### 6.1 Municipal & Organic Waste
- Wet food waste from student dining halls is routed to on-site biomethanation or vermicomposting facilities, generating organic compost for campus landscaping.
- Dry recyclables (paper, cardboard, plastics, metals) are baled and transferred to authorized recyclers with weighing slip reconciliation.

### 6.2 Hazardous & Regulated Waste (SPCB Rules)
- Laboratory chemical effluents, spent solvents, heavy metal residues, and expired chemicals require strict compliance with Hazardous and Other Wastes (Management and Transboundary Movement) Rules.
- **Form 10 Manifest**: Requires capturing the official State Pollution Control Board manifest reference number (`tsdf_manifest_number`), transporter registration, authorized Treatment, Storage, and Disposal Facility (TSDF) destination, and disposal certificate attachment URL.
- CampusOS prohibits closing a hazardous waste batch without a valid TSDF manifest reference.

---

## 7. IoT Smart Meter Gateway & Cryptographic Deduplication

High-frequency telemetry ingestion from campus building sub-meters, Modbus RTU/TCP gateways, and LoRaWAN environmental nodes is received at:
`POST /api/v1/sustainability/iot/ingest`

### 7.1 Security & Authentication
- Every smart meter possesses an encrypted `device_secret` issued during commissioning.
- Meter gateways submit telemetry accompanied by timestamped HMAC-SHA256 signatures or SHA-256 payload hashes.

### 7.2 Cryptographic Deduplication
To prevent duplicate readings caused by network retries or gateway reboots, the service computes:
$$\text{Payload Hash} = \text{SHA256}(\text{meter\_id} \parallel \text{reading\_timestamp} \parallel \text{value})$$
If an event with the identical hash already exists in `iot_ingestion_events`, the incoming packet is tagged as `DUPLICATE` and discarded without creating redundant resource measurements or skewing energy totals.

---

## 8. Role-Based Access Control (RBAC) & Permissions

Step 67 introduces 19 granular permissions registered in `apps/api/app/core/permissions.py`:

| Permission Code | Dot-Notation Alias | Description | Roles Assigned |
| :--- | :--- | :--- | :--- |
| `SUSTAINABILITY_TARGET_READ` | `sustainability:target:read` | View institutional sustainability profiles and reduction targets | Super Admin, Institution Admin, Compliance Officer, Sustainability Coordinator, Faculty |
| `SUSTAINABILITY_TARGET_MANAGE` | `sustainability:target:manage` | Configure baselines, net-zero deadlines, and goals | Super Admin, Institution Admin, Sustainability Coordinator |
| `SUSTAINABILITY_ENERGY_READ` | `sustainability:energy:read` | View energy consumption, solar yield, and peak loads | Super Admin, Institution Admin, Compliance Officer, Sustainability Coordinator, Facilities Manager |
| `SUSTAINABILITY_ENERGY_MANAGE` | `sustainability:energy:manage` | Log energy readings, calibrate meters, resolve anomalies | Super Admin, Institution Admin, Sustainability Coordinator, Facilities Manager |
| `SUSTAINABILITY_WATER_READ` | `sustainability:water:read` | Inspect water balance, borewell extraction, STP reuse | Super Admin, Institution Admin, Compliance Officer, Sustainability Coordinator |
| `SUSTAINABILITY_WATER_MANAGE` | `sustainability:water:manage` | Log water readings and manage leak incident CAPA | Super Admin, Institution Admin, Sustainability Coordinator, Facilities Manager |
| `SUSTAINABILITY_WASTE_READ` | `sustainability:waste:read` | View waste generation and recycling metrics | Super Admin, Institution Admin, Compliance Officer, Sustainability Coordinator |
| `SUSTAINABILITY_WASTE_MANAGE` | `sustainability:waste:manage` | Record waste collections and organic composting logs | Super Admin, Institution Admin, Sustainability Coordinator |
| `SUSTAINABILITY_WASTE_HAZARDOUS` | `sustainability:waste:hazardous` | Authorize hazardous TSDF Form 10 manifests | Super Admin, Institution Admin, Compliance Officer |
| `SUSTAINABILITY_EMISSIONS_READ` | `sustainability:emissions:read` | View Scope 1, 2, 3 carbon calculations and reports | Super Admin, Institution Admin, Compliance Officer, Sustainability Coordinator |
| `SUSTAINABILITY_EMISSIONS_CALCULATE` | `sustainability:emissions:calculate` | Execute GHG calculations and seal audit digests | Super Admin, Institution Admin, Sustainability Coordinator |
| `SUSTAINABILITY_EMISSIONS_FACTOR_MANAGE`| `sustainability:emissions_factor:manage`| Update emission factors and conversion standards | Super Admin, Institution Admin, Sustainability Coordinator |
| `SUSTAINABILITY_INITIATIVE_READ` | `sustainability:initiative:read` | View green capital portfolio and avoided carbon | Super Admin, Institution Admin, Compliance Officer, Sustainability Coordinator |
| `SUSTAINABILITY_INITIATIVE_MANAGE` | `sustainability:initiative:manage` | Create initiatives, allocate capex, update milestones| Super Admin, Institution Admin, Sustainability Coordinator |
| `SUSTAINABILITY_COMPLIANCE_READ` | `sustainability:compliance:read` | View SPCB/CGWA environmental permits and licenses | Super Admin, Institution Admin, Compliance Officer, Sustainability Coordinator |
| `SUSTAINABILITY_COMPLIANCE_MANAGE` | `sustainability:compliance:manage` | File permits, log renewals, assign CAPA actions | Super Admin, Institution Admin, Compliance Officer |
| `SUSTAINABILITY_IOT_INGEST` | `sustainability:iot:ingest` | Authorize IoT meter telemetry streams | Super Admin, Institution Admin, Sustainability Coordinator, IoT Service Account |
| `SUSTAINABILITY_DATA_IMPORT` | `sustainability:data:import` | Import utility invoice CSV reconciliation batches | Super Admin, Institution Admin, Sustainability Coordinator |
| `SUSTAINABILITY_ANALYTICS_READ` | `sustainability:analytics:read` | Access executive ESG scorecard and EUI heatmaps | Super Admin, Institution Admin, Vice Principal, Compliance Officer, Sustainability Coordinator |

---

## 9. Verification & Automated Test Evidence

### 9.1 Backend Pytest Test Suite
Executed via: `apps/api/.venv/Scripts/python.exe -m pytest apps/api/tests/test_enterprise_sustainability_step67.py -v`
- **Result:** 11 passed in 16.92s.
- **Test Scenarios Covered:**
  1. `test_get_sustainability_overview`: Validates ESG composite score, statutory compliance percentage, and real-time solar share.
  2. `test_create_sustainability_profile`: Confirms baseline year, net-zero deadline, and institutional reduction targets.
  3. `test_create_sustainability_target`: Validates granular target creation, baseline tracking, and progress metrics.
  4. `test_emission_factors_registry`: Confirms registration of CEA India grid factors and diesel combustion factors.
  5. `test_record_resource_measurement_with_anomaly_detection`: Confirms anomaly classification: normal reading (NORMAL), +36.7% spike (WARNING), and +73.3% spike (CRITICAL).
  6. `test_water_incident_lifecycle`: Tests detection, loss volume assessment, and remediation closure.
  7. `test_hazardous_waste_tsdf_tracking`: Enforces SPCB Form 10 TSDF manifests and disposal certificate validation.
  8. `test_carbon_emissions_calculation_and_audit_hash`: Validates Scope 1, 2, 3 carbon math and SHA-256 cryptographic audit seal generation.
  9. `test_sustainability_initiative_creation`: Verifies capital budget, annual avoided carbon (MT CO2e), and payback period computation.
  10. `test_environmental_compliance_and_corrective_action`: Verifies statutory Consent to Operate (CTO) permits and High-priority CAPA actions.
  11. `test_iot_meter_ingestion_and_deduplication`: Verifies cryptographic SHA-256 payload deduplication preventing duplicate energy logs.

### 9.2 Frontend Automation Test Suite
Executed via: `npx tsx apps/web/src/__tests__/sustainability-module.test.ts`
- **Result:** 63 passed, 0 failed.
- **Frontend Pages Verified:**
  1. `/app/sustainability` (Executive Hub & Composite ESG Scorecard)
  2. `/app/sustainability/targets` (Decarbonization Targets & Baselines)
  3. `/app/sustainability/energy` (Multi-Source Energy & Anomaly Detection)
  4. `/app/sustainability/water` (Water Balance & Leak Mitigation)
  5. `/app/sustainability/waste` (Circularity & Hazardous TSDF Manifests)
  6. `/app/sustainability/carbon` (GHG Protocol Scope 1/2/3 Calculator & Factor Registry)
  7. `/app/sustainability/initiatives` (Decarbonization Capital Portfolio)
  8. `/app/sustainability/compliance` (Statutory SPCB/CGWA Permits & CAPA Actions)
  9. `/app/sustainability/iot-meters` (IoT Smart Meter Stream & Deduplication Log)
  10. `/app/sustainability/imports` (Utility Invoice CSV Reconciliation)
  11. `/app/sustainability/analytics` (Building EUI Heatmap & Decarbonization Glidepath)

### 9.3 Regression Test Verification (Step 66)
Executed via: `npx tsx apps/web/src/__tests__/housing-module.test.ts`
- **Result:** 66 passed, 0 failed.
- Confirmed backward compatibility across accommodation providers, property lifecycle transitions, addressable bed allocations, digital leases, and safety inspections.

### 9.4 TypeScript Compilation
Executed via: `npx tsc --noEmit -p apps/web/tsconfig.json`
- **Result:** 0 errors (clean compilation).

---

## 10. Operational Runbook & Maintenance

### 10.1 Daily Operating Checklist
1. **Anomaly Queue Review**: Inspect `/app/sustainability/energy` for any `WARNING` or `CRITICAL` load spikes. Verify if an automated facilities work order was triggered.
2. **Water Infrastructure Audit**: Check `/app/sustainability/water` for open leak incidents. Ensure emergency plumbing contractors or in-house facilities teams have acknowledged alerts.
3. **IoT Gateway Health**: Confirm smart meter heartbeat timestamps in `/app/sustainability/iot-meters`. If any meter is marked `OFFLINE`, dispatch local electrical technicians to inspect RS485 Modbus converters or local WiFi/Ethernet drops.

### 10.2 Monthly Regulatory Reporting & Closure
1. **Utility Invoice Reconciliation**: Upload electricity, piped gas, and municipal water utility bills via `/app/sustainability/imports`. Reconcile invoice units against physical sub-meter aggregations.
2. **Execute GHG Protocol Period Run**: Run the carbon calculation in `/app/sustainability/carbon`. Ensure the generated SHA-256 audit digest is recorded and archive the monthly emission report.
3. **Statutory Permit Review**: Check `/app/sustainability/compliance` for any SPCB Consent to Operate (CTO) or CGWA groundwater NOCs expiring within 90 days. Initiate renewal workflows.
4. **Hazardous Manifest Verification**: Audit laboratory chemical and e-waste disposals in `/app/sustainability/waste`. Confirm all Form 10 manifests have verified TSDF disposal certificates attached.

---

**CampusOS Operations Directorate**  
*One Campus. One System. One Source of Truth.*

